This model defines the database-level structure that corresponds to the conceptual UML class diagram.

-----

## Patient
- PK: patient_id
- Attributes: name, dob
- Relationships: one patient, many procedures

## Procedure
- PK: procedure_id
- FK: patient_id -> Patient
- Attributes: type, scheduled_at
- Each procedure belongs to one patient and contains multiple ultrasound frames

## UltrasoundFrame
- PK: frame_id
- FK: procedure_id -> Procedure, device_id -> Device
- Attributes: timestamp, image_uri, width, height, format
- Each procedure generates many frames, each frame has one FramePose

## FramePose
- PK: pose_id
- FK: frame_id -> UltrasoundFrame, device_id -> Device
- Attributes: timestamp, pose_matrix, quality_score

## Calibration
- PK: calib_id
- FK: device_id -> Device
- Attributes: version, created_at, params_uri

## ReconstructionJob
- PK: recon_id
- FK: calib_id -> Calibration
- Attributes: started_at, finished_at, status
- One job produces exactly one Volume3D

## Volume3D
- PK: volume_id
- FK: recon_id -> ReconstructionJob
- Attributes: grid_uri, voxel_size, created_at
- One volume can have multiple segmentations, registrations, and navigation sessions

## Segmentation
- PK: seg_id
- FK: volume_id -> Volume3D
- Attributes: label, created_at

## Registration
- PK: reg_id
- FK: volume_id -> Volume3D
- Attributes: target_frame, transform_uri, fiducial_error

## NavigationSession
- PK: session_id
- FK: volume_id -> Volume3D, started_by_user_id -> User
- Attributes: start_time, end_time, status

## InstrumentPose
- PK: ip_id
- FK: session_id -> NavigationSession
- Attributes: timestamp, pose_matrix

## Log
- PK: log_id
- FK: session_id -> NavigationSession
- Attributes: timestamp, level, event_type

## User
- PK: user_id
- Attributes: name, role