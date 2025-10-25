These rules define the constraints and validity checks applied to all data entities to ensure consistency, reliability, and referential integrity.

-----

## Uniqueness and Key Integrity
- All primary keys (ex. patient_id, procedure_id) must be globally unique.
- Each foreign key must reference exactly one valid parent record.
- One-to-one relationships must maintain mutual uniqueness.

## Referential Integrity
- Every foreign key must reference an existing parent record.
- Deleting a parent record must cascade or restrict deletion to maintain integrity:
    - Patient deletion restricted if Procedures exist
    - Volume3D deltetion restricted if Segmentations or Registrations exist

## Allowed Ranges and Valid Values
- Timestamps must be valid ISO-8601 values and non-future for completed jobs.
- FiducialError in Registration must be ≤ 2.0 mm (target precision).
- Status values must match enumerations:
    - ReconstructionJob.status ∈ {queued, running, failed, success}
    - NavigationSession.status ∈ {active, completed, aborted}
- User.role ∈ {SURGEON, TECH, ADMIN}

## Default behaviours
- ReconstructionJob.status defaults to "queued."
- NavigationSession.status defaults to "active" at creation.

## Data Consistency and Completeness
- FramePose.timestamp and UltrasoundFrame.timestamp must differ by less than 25 ms to preserve frame-pose sync.
- Each Volume3D must have a valid Calibration.version associated with its ReconstructionJob.
- All grid_uri, image_uri, and mask_uri values must be reachable paths or verified object-store URIs.

## Audie and Provenance
- All NavigationSessions must include at least one Log entry.
- Every modification to Calibration or Volume3D must generate an audit Log entry.