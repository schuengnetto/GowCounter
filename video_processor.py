import cv2
from ultralytics import YOLO
import datetime
from database import save_detection

# Load YOLOv8 nano model for speed
model = YOLO('yolov8n.pt')

# Create a custom config file for ByteTrack to increase occlusion tolerance
custom_tracker_path = "custom_bytetrack.yaml"
with open(custom_tracker_path, "w") as f:
    f.write("""
tracker_type: bytetrack
track_high_thresh: 0.3    # Lower threshold to pick up partially occluded objects
track_low_thresh: 0.1
new_track_thresh: 0.4
track_buffer: 120         # Increase memory to 120 frames (allows object to be hidden behind a car for seconds and keep ID)
match_thresh: 0.95        # Be very lenient in matching bounding boxes
fuse_score: True          # Required parameter to prevent crash
""")


def process_video_generator(video_path, video_name, start_time: datetime.datetime, end_time: datetime.datetime):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Erro ao abrir vídeo.")
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    user_duration = (end_time - start_time).total_seconds()
    
    frame_index = 0
    tracked_ids = set()
    track_history = {}
    
    # Dynamic MIN_FRAMES depending on object class (people appear briefly, cars are large)
    def get_min_frames(class_name):
        if class_name == 'Pessoa':
            return 3  # Count people quicker before they get occluded
        elif class_name == 'Bicicleta':
            return 4
        return 8      # Strict counting for cars to avoid double counting

    # Model tracking objects: 0:person, 1:bicycle, 2:car, 3:motorcycle, 5:bus, 7:truck
    vid_stride = 3
    results = model.track(
        source=video_path, 
        stream=True, 
        persist=True, 
        classes=[0, 1, 2, 3, 5, 7], 
        verbose=False,
        tracker=custom_tracker_path, # Use the custom configuration with high occlusion tolerance
        conf=0.35, # Lowered confidence to 0.35 to catch more people
        iou=0.6,   # Lower NMS overlap to prevent one box suppressing another slightly behind it
        imgsz=480,
        vid_stride=vid_stride
    )
    
    class_map = {
        0: 'Pessoa',
        1: 'Bicicleta',
        2: 'Automóvel',
        3: 'Automóvel',
        5: 'Automóvel',
        7: 'Automóvel'
    }

    for result in results:
        frame_index += vid_stride
        
        progress_ratio = frame_index / total_frames if total_frames > 0 else 0
        current_time = start_time + datetime.timedelta(seconds=user_duration * progress_ratio)
        
        boxes = result.boxes
        if boxes is not None and boxes.id is not None:
            track_ids = boxes.id.int().cpu().tolist()
            class_ids = boxes.cls.int().cpu().tolist()
            
            for t_id, c_id in zip(track_ids, class_ids):
                if c_id in class_map:
                    obj_type = class_map[c_id]
                    unique_id = f"{video_name}_{obj_type}_{t_id}"
                    
                    if unique_id not in tracked_ids:
                        if unique_id not in track_history:
                            track_history[unique_id] = 0
                        track_history[unique_id] += 1
                        
                        dynamic_min = get_min_frames(obj_type)
                        if track_history[unique_id] >= dynamic_min:
                            tracked_ids.add(unique_id)
                            save_detection(video_name, obj_type, current_time.strftime("%Y-%m-%d %H:%M:%S"), t_id)
        
        annotated_frame = result.plot()
        annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        
        yield annotated_frame, frame_index, total_frames

    cap.release()
