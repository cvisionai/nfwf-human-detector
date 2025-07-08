import os
import time
import requests
import subprocess
from celery import Celery
from celery import current_task
import csv
import time
import re
import glob

# Create the Celery application
celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")


@celery.task(name="create_task")
def create_task(task_type):
    time.sleep(int(task_type) * 10)
    return True

@celery.task(bind=True, name="slice_video")
def slice_video(self, fileName, start_frame, end_frame, output_filename):

    file_path = os.path.join('/inputs',fileName)

    ffprobe_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    #output = subprocess.check_output(ffprobe_cmd)
    output = subprocess.check_output(ffprobe_cmd).decode('utf-8')
    fps, duration = map(float, output.strip().split('\n'))
    #fps = float(eval(output))

    start_time = start_frame / fps
    end_time = end_frame / fps
    ffmpeg_cmd = ['ffmpeg', '-i', file_path, '-ss', str(start_time), '-t', str(end_time - start_time), '/outputs/' + output_filename]
    try:
        subprocess.run(ffmpeg_cmd)
    except subprocess.CalledProcessError as e:
        self.update_state(state='FAILURE', 
            meta={'status': 'Failed',
            'exc_type': type(e).__name__,
            'exc_message': e.output.decode('utf-8').split('\n'),
            'custom': '...'
            })
        return False

    # Return the output filename so the API can include it in the response
    return output_filename

@celery.task(bind=True, name="run_yolo", result_extended=True)
def run_yolo(self, video_path, confidence=0.25):

    video_path = os.path.join('/inputs',video_path)

    # Check if the video path is a folder or file
    if os.path.isdir(video_path):
        # Create list of video files in the path
        video_files = [os.path.join(video_path,f) for f in os.listdir(video_path) if os.path.isfile(os.path.join(video_path, f))]
    else:
        video_files = [video_path]

    for video_file in video_files:
        
        weights_path = '/work/yolov5/yolov5l6.pt'
        strategy = {
            'image_size': 1280,
            'classes': [0],
            'vid_stride': 1,
            'conf_thres': confidence,
            }
        
        cmd=["python3",
                "/work/yolov5/detect.py",
                "--weights", str(weights_path),
                "--source", str(video_file),
                "--project", "/outputs",
                "--name", os.path.splitext(video_file.split('/')[-1])[0],
                "--save-txt", # Save text output (localizations)
                "--save-conf", # With confidences
                "--nosave", # Don't save images/video
                "--device", "0"
            ]
    
        image_size = strategy.get('image_size',None)
        if type(image_size) == list:
            for sz in image_size:
                cmd.extend(["--imgsz", str(sz)])
        elif image_size:
            cmd.extend(["--imgsz", str(image_size)])

        conf_thresh = strategy.get('conf_thres',None)
        if conf_thresh is not None:
            cmd.extend(["--conf-thres", str(conf_thresh)])
        
        classes = strategy.get('classes', None)
        if type(classes) == list:
            cmd.extend(["--classes"])
            for elem in classes:
                cmd.extend([str(elem)])
        elif classes is not None:
            cmd.extend(['--classes', str(classes)])

        # Get the video duration and fps
        ffprobe_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate,duration", "-of", "default=noprint_wrappers=1:nokey=1", video_file]
        output = subprocess.check_output(ffprobe_cmd).decode('utf-8')
        output_lines = output.strip().split('\n')
        fps = float(eval(output_lines[0]))
        duration = float(output_lines[1])
        #fps, duration = map(float, eval(output.strip().split('\n')))
        num_samples = int(duration/strategy.get('vid_stride', 1))
        # Set vid_stride based off desired sampling rate from strategy and video fps
        vid_stride = int(strategy.get('vid_stride', 1) * fps)

        #vid_stride = strategy.get('vid_stride', None)
        if vid_stride is not None:
            cmd.extend(['--vid-stride', str(vid_stride)])

        print(f"CMD={cmd}")

        self.update_state(state='PROGRESS', meta={'status': 'Starting YOLO'})

        try:
            process = subprocess.Popen(cmd, cwd='/work/yolov5')

            while True:
                # Check if the process has finished
                if process.poll() is not None:
                    break

                directory = f'/outputs/{os.path.splitext(video_file.split("/")[-1])[0]}/labels'
                tmp_files = glob.glob(os.path.join(directory, '*.txt'))

                numbers = [int(re.search(r'_(\d+)\.txt$', file).group(1)) for file in tmp_files if re.search(r'_(\d+)\.txt$', file)]

                # Get the highest number
                highest_number = max(numbers) if numbers else 0

                # Calculate the percentage
                percentage = highest_number / num_samples * 100

                # Update the task state
                self.update_state(state='PROGRESS', meta={'status': f'Video Duration: {duration:.1f}s, Num Samples: {num_samples}, Sample Rate: {strategy.get("vid_stride", 1)}s, Percent Complete: {percentage:.1f}%'})

                # Wait a bit before checking again
                time.sleep(1)

        except subprocess.CalledProcessError as e:
            self.update_state(state='FAILURE', 
                meta={'status': 'Failed',
                'exc_type': type(e).__name__,
                'exc_message': e.output.decode('utf-8').split('\n'),
                'custom': '...'
                })
            return False
        
        # Concatenate the list of text files into a single file in the output directory
        results_dir = f'/outputs/{os.path.splitext(video_file.split("/")[-1])[0]}'
        # Write json file that has duration and number of samples
        with open(os.path.join(results_dir,'metadata.json'), 'w') as outfile:
            outfile.write(f'{{"duration": {duration}, "num_samples": {num_samples}, "sample_rate": {strategy.get("vid_stride", 1)}}}')
        with open(os.path.join(results_dir,'labels.csv'), 'w', newline='') as outfile:
            writer = csv.writer(outfile)
            for fname in os.listdir(f'/outputs/{os.path.splitext(video_file.split("/")[-1])[0]}/labels'):
                if fname.endswith('.txt'):
                    with open(f'/outputs/{os.path.splitext(video_file.split("/")[-1])[0]}/labels/{fname}') as infile:
                        lines = infile.readlines()
                        max_line = max(lines, key=lambda line: float(line.split()[-1]))
                        confidence = float(max_line.split()[-1])
                        sample_num = int(fname.split('.')[0].split("_")[-1])
                        writer.writerow([sample_num, confidence])
                    # Once finished, delete the text file
                    #os.remove(f'/outputs/{os.path.splitext(video_file.split("/")[-1])[0]}/labels/{fname}')

    
    return "Completed"