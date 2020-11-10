# Copyright 2020  Ternaris.
# SPDX-License-Identifier: Apache-2.0
#
# THIS FILE IS GENERATED, DO NOT EDIT

"""ROS2 + Autoware.Auto message types."""

# pylint: disable=too-many-lines,invalid-name,too-many-instance-attributes

from dataclasses import dataclass
from typing import Any


@dataclass
class builtin_interfaces__msg__Time:
    """Class for builtin_interfaces/msg/Time."""

    sec: Any
    nanosec: Any


@dataclass
class builtin_interfaces__msg__Duration:
    """Class for builtin_interfaces/msg/Duration."""

    sec: Any
    nanosec: Any


@dataclass
class diagnostic_msgs__msg__DiagnosticStatus:
    """Class for diagnostic_msgs/msg/DiagnosticStatus."""

    level: Any
    name: Any
    message: Any
    hardware_id: Any
    values: Any


@dataclass
class diagnostic_msgs__msg__DiagnosticArray:
    """Class for diagnostic_msgs/msg/DiagnosticArray."""

    header: Any
    status: Any


@dataclass
class diagnostic_msgs__msg__KeyValue:
    """Class for diagnostic_msgs/msg/KeyValue."""

    key: Any
    value: Any


@dataclass
class geometry_msgs__msg__AccelWithCovariance:
    """Class for geometry_msgs/msg/AccelWithCovariance."""

    accel: Any
    covariance: Any


@dataclass
class geometry_msgs__msg__Point32:
    """Class for geometry_msgs/msg/Point32."""

    x: Any
    y: Any
    z: Any


@dataclass
class geometry_msgs__msg__Vector3:
    """Class for geometry_msgs/msg/Vector3."""

    x: Any
    y: Any
    z: Any


@dataclass
class geometry_msgs__msg__Inertia:
    """Class for geometry_msgs/msg/Inertia."""

    m: Any
    com: Any
    ixx: Any
    ixy: Any
    ixz: Any
    iyy: Any
    iyz: Any
    izz: Any


@dataclass
class geometry_msgs__msg__PoseWithCovarianceStamped:
    """Class for geometry_msgs/msg/PoseWithCovarianceStamped."""

    header: Any
    pose: Any


@dataclass
class geometry_msgs__msg__Twist:
    """Class for geometry_msgs/msg/Twist."""

    linear: Any
    angular: Any


@dataclass
class geometry_msgs__msg__Pose:
    """Class for geometry_msgs/msg/Pose."""

    position: Any
    orientation: Any


@dataclass
class geometry_msgs__msg__Point:
    """Class for geometry_msgs/msg/Point."""

    x: Any
    y: Any
    z: Any


@dataclass
class geometry_msgs__msg__Vector3Stamped:
    """Class for geometry_msgs/msg/Vector3Stamped."""

    header: Any
    vector: Any


@dataclass
class geometry_msgs__msg__Transform:
    """Class for geometry_msgs/msg/Transform."""

    translation: Any
    rotation: Any


@dataclass
class geometry_msgs__msg__PolygonStamped:
    """Class for geometry_msgs/msg/PolygonStamped."""

    header: Any
    polygon: Any


@dataclass
class geometry_msgs__msg__Quaternion:
    """Class for geometry_msgs/msg/Quaternion."""

    x: Any
    y: Any
    z: Any
    w: Any


@dataclass
class geometry_msgs__msg__Pose2D:
    """Class for geometry_msgs/msg/Pose2D."""

    x: Any
    y: Any
    theta: Any


@dataclass
class geometry_msgs__msg__InertiaStamped:
    """Class for geometry_msgs/msg/InertiaStamped."""

    header: Any
    inertia: Any


@dataclass
class geometry_msgs__msg__TwistStamped:
    """Class for geometry_msgs/msg/TwistStamped."""

    header: Any
    twist: Any


@dataclass
class geometry_msgs__msg__PoseStamped:
    """Class for geometry_msgs/msg/PoseStamped."""

    header: Any
    pose: Any


@dataclass
class geometry_msgs__msg__PointStamped:
    """Class for geometry_msgs/msg/PointStamped."""

    header: Any
    point: Any


@dataclass
class geometry_msgs__msg__Polygon:
    """Class for geometry_msgs/msg/Polygon."""

    points: Any


@dataclass
class geometry_msgs__msg__PoseArray:
    """Class for geometry_msgs/msg/PoseArray."""

    header: Any
    poses: Any


@dataclass
class geometry_msgs__msg__AccelStamped:
    """Class for geometry_msgs/msg/AccelStamped."""

    header: Any
    accel: Any


@dataclass
class geometry_msgs__msg__TwistWithCovarianceStamped:
    """Class for geometry_msgs/msg/TwistWithCovarianceStamped."""

    header: Any
    twist: Any


@dataclass
class geometry_msgs__msg__QuaternionStamped:
    """Class for geometry_msgs/msg/QuaternionStamped."""

    header: Any
    quaternion: Any


@dataclass
class geometry_msgs__msg__WrenchStamped:
    """Class for geometry_msgs/msg/WrenchStamped."""

    header: Any
    wrench: Any


@dataclass
class geometry_msgs__msg__AccelWithCovarianceStamped:
    """Class for geometry_msgs/msg/AccelWithCovarianceStamped."""

    header: Any
    accel: Any


@dataclass
class geometry_msgs__msg__PoseWithCovariance:
    """Class for geometry_msgs/msg/PoseWithCovariance."""

    pose: Any
    covariance: Any


@dataclass
class geometry_msgs__msg__Wrench:
    """Class for geometry_msgs/msg/Wrench."""

    force: Any
    torque: Any


@dataclass
class geometry_msgs__msg__TransformStamped:
    """Class for geometry_msgs/msg/TransformStamped."""

    header: Any
    child_frame_id: Any
    transform: Any


@dataclass
class geometry_msgs__msg__Accel:
    """Class for geometry_msgs/msg/Accel."""

    linear: Any
    angular: Any


@dataclass
class geometry_msgs__msg__TwistWithCovariance:
    """Class for geometry_msgs/msg/TwistWithCovariance."""

    twist: Any
    covariance: Any


@dataclass
class libstatistics_collector__msg__DummyMessage:
    """Class for libstatistics_collector/msg/DummyMessage."""

    header: Any


@dataclass
class lifecycle_msgs__msg__TransitionDescription:
    """Class for lifecycle_msgs/msg/TransitionDescription."""

    transition: Any
    start_state: Any
    goal_state: Any


@dataclass
class lifecycle_msgs__msg__State:
    """Class for lifecycle_msgs/msg/State."""

    id: Any
    label: Any


@dataclass
class lifecycle_msgs__msg__TransitionEvent:
    """Class for lifecycle_msgs/msg/TransitionEvent."""

    timestamp: Any
    transition: Any
    start_state: Any
    goal_state: Any


@dataclass
class lifecycle_msgs__msg__Transition:
    """Class for lifecycle_msgs/msg/Transition."""

    id: Any
    label: Any


@dataclass
class nav_msgs__msg__MapMetaData:
    """Class for nav_msgs/msg/MapMetaData."""

    map_load_time: Any
    resolution: Any
    width: Any
    height: Any
    origin: Any


@dataclass
class nav_msgs__msg__GridCells:
    """Class for nav_msgs/msg/GridCells."""

    header: Any
    cell_width: Any
    cell_height: Any
    cells: Any


@dataclass
class nav_msgs__msg__Odometry:
    """Class for nav_msgs/msg/Odometry."""

    header: Any
    child_frame_id: Any
    pose: Any
    twist: Any


@dataclass
class nav_msgs__msg__Path:
    """Class for nav_msgs/msg/Path."""

    header: Any
    poses: Any


@dataclass
class nav_msgs__msg__OccupancyGrid:
    """Class for nav_msgs/msg/OccupancyGrid."""

    header: Any
    info: Any
    data: Any


@dataclass
class rcl_interfaces__msg__ListParametersResult:
    """Class for rcl_interfaces/msg/ListParametersResult."""

    names: Any
    prefixes: Any


@dataclass
class rcl_interfaces__msg__ParameterType:
    """Class for rcl_interfaces/msg/ParameterType."""

    structure_needs_at_least_one_member: Any


@dataclass
class rcl_interfaces__msg__ParameterEventDescriptors:
    """Class for rcl_interfaces/msg/ParameterEventDescriptors."""

    new_parameters: Any
    changed_parameters: Any
    deleted_parameters: Any


@dataclass
class rcl_interfaces__msg__ParameterEvent:
    """Class for rcl_interfaces/msg/ParameterEvent."""

    stamp: Any
    node: Any
    new_parameters: Any
    changed_parameters: Any
    deleted_parameters: Any


@dataclass
class rcl_interfaces__msg__IntegerRange:
    """Class for rcl_interfaces/msg/IntegerRange."""

    from_value: Any
    to_value: Any
    step: Any


@dataclass
class rcl_interfaces__msg__Parameter:
    """Class for rcl_interfaces/msg/Parameter."""

    name: Any
    value: Any


@dataclass
class rcl_interfaces__msg__ParameterValue:
    """Class for rcl_interfaces/msg/ParameterValue."""

    type: Any
    bool_value: Any
    integer_value: Any
    double_value: Any
    string_value: Any
    byte_array_value: Any
    bool_array_value: Any
    integer_array_value: Any
    double_array_value: Any
    string_array_value: Any


@dataclass
class rcl_interfaces__msg__FloatingPointRange:
    """Class for rcl_interfaces/msg/FloatingPointRange."""

    from_value: Any
    to_value: Any
    step: Any


@dataclass
class rcl_interfaces__msg__SetParametersResult:
    """Class for rcl_interfaces/msg/SetParametersResult."""

    successful: Any
    reason: Any


@dataclass
class rcl_interfaces__msg__Log:
    """Class for rcl_interfaces/msg/Log."""

    stamp: Any
    level: Any
    name: Any
    msg: Any
    file: Any
    function: Any
    line: Any


@dataclass
class rcl_interfaces__msg__ParameterDescriptor:
    """Class for rcl_interfaces/msg/ParameterDescriptor."""

    name: Any
    type: Any
    description: Any
    additional_constraints: Any
    read_only: Any
    floating_point_range: Any
    integer_range: Any


@dataclass
class rmw_dds_common__msg__Gid:
    """Class for rmw_dds_common/msg/Gid."""

    data: Any


@dataclass
class rmw_dds_common__msg__NodeEntitiesInfo:
    """Class for rmw_dds_common/msg/NodeEntitiesInfo."""

    node_namespace: Any
    node_name: Any
    reader_gid_seq: Any
    writer_gid_seq: Any


@dataclass
class rmw_dds_common__msg__ParticipantEntitiesInfo:
    """Class for rmw_dds_common/msg/ParticipantEntitiesInfo."""

    gid: Any
    node_entities_info_seq: Any


@dataclass
class rosgraph_msgs__msg__Clock:
    """Class for rosgraph_msgs/msg/Clock."""

    clock: Any


@dataclass
class sensor_msgs__msg__Temperature:
    """Class for sensor_msgs/msg/Temperature."""

    header: Any
    temperature: Any
    variance: Any


@dataclass
class sensor_msgs__msg__Range:
    """Class for sensor_msgs/msg/Range."""

    header: Any
    radiation_type: Any
    field_of_view: Any
    min_range: Any
    max_range: Any
    range: Any


@dataclass
class sensor_msgs__msg__RegionOfInterest:
    """Class for sensor_msgs/msg/RegionOfInterest."""

    x_offset: Any
    y_offset: Any
    height: Any
    width: Any
    do_rectify: Any


@dataclass
class sensor_msgs__msg__JoyFeedbackArray:
    """Class for sensor_msgs/msg/JoyFeedbackArray."""

    array: Any


@dataclass
class sensor_msgs__msg__TimeReference:
    """Class for sensor_msgs/msg/TimeReference."""

    header: Any
    time_ref: Any
    source: Any


@dataclass
class sensor_msgs__msg__CompressedImage:
    """Class for sensor_msgs/msg/CompressedImage."""

    header: Any
    format: Any
    data: Any


@dataclass
class sensor_msgs__msg__MultiEchoLaserScan:
    """Class for sensor_msgs/msg/MultiEchoLaserScan."""

    header: Any
    angle_min: Any
    angle_max: Any
    angle_increment: Any
    time_increment: Any
    scan_time: Any
    range_min: Any
    range_max: Any
    ranges: Any
    intensities: Any


@dataclass
class sensor_msgs__msg__LaserEcho:
    """Class for sensor_msgs/msg/LaserEcho."""

    echoes: Any


@dataclass
class sensor_msgs__msg__ChannelFloat32:
    """Class for sensor_msgs/msg/ChannelFloat32."""

    name: Any
    values: Any


@dataclass
class sensor_msgs__msg__CameraInfo:
    """Class for sensor_msgs/msg/CameraInfo."""

    header: Any
    height: Any
    width: Any
    distortion_model: Any
    d: Any
    k: Any
    r: Any
    p: Any
    binning_x: Any
    binning_y: Any
    roi: Any


@dataclass
class sensor_msgs__msg__RelativeHumidity:
    """Class for sensor_msgs/msg/RelativeHumidity."""

    header: Any
    relative_humidity: Any
    variance: Any


@dataclass
class sensor_msgs__msg__FluidPressure:
    """Class for sensor_msgs/msg/FluidPressure."""

    header: Any
    fluid_pressure: Any
    variance: Any


@dataclass
class sensor_msgs__msg__LaserScan:
    """Class for sensor_msgs/msg/LaserScan."""

    header: Any
    angle_min: Any
    angle_max: Any
    angle_increment: Any
    time_increment: Any
    scan_time: Any
    range_min: Any
    range_max: Any
    ranges: Any
    intensities: Any


@dataclass
class sensor_msgs__msg__BatteryState:
    """Class for sensor_msgs/msg/BatteryState."""

    header: Any
    voltage: Any
    temperature: Any
    current: Any
    charge: Any
    capacity: Any
    design_capacity: Any
    percentage: Any
    power_supply_status: Any
    power_supply_health: Any
    power_supply_technology: Any
    present: Any
    cell_voltage: Any
    cell_temperature: Any
    location: Any
    serial_number: Any


@dataclass
class sensor_msgs__msg__Image:
    """Class for sensor_msgs/msg/Image."""

    header: Any
    height: Any
    width: Any
    encoding: Any
    is_bigendian: Any
    step: Any
    data: Any


@dataclass
class sensor_msgs__msg__PointCloud:
    """Class for sensor_msgs/msg/PointCloud."""

    header: Any
    points: Any
    channels: Any


@dataclass
class sensor_msgs__msg__Imu:
    """Class for sensor_msgs/msg/Imu."""

    header: Any
    orientation: Any
    orientation_covariance: Any
    angular_velocity: Any
    angular_velocity_covariance: Any
    linear_acceleration: Any
    linear_acceleration_covariance: Any


@dataclass
class sensor_msgs__msg__NavSatStatus:
    """Class for sensor_msgs/msg/NavSatStatus."""

    status: Any
    service: Any


@dataclass
class sensor_msgs__msg__Illuminance:
    """Class for sensor_msgs/msg/Illuminance."""

    header: Any
    illuminance: Any
    variance: Any


@dataclass
class sensor_msgs__msg__Joy:
    """Class for sensor_msgs/msg/Joy."""

    header: Any
    axes: Any
    buttons: Any


@dataclass
class sensor_msgs__msg__NavSatFix:
    """Class for sensor_msgs/msg/NavSatFix."""

    header: Any
    status: Any
    latitude: Any
    longitude: Any
    altitude: Any
    position_covariance: Any
    position_covariance_type: Any


@dataclass
class sensor_msgs__msg__MultiDOFJointState:
    """Class for sensor_msgs/msg/MultiDOFJointState."""

    header: Any
    joint_names: Any
    transforms: Any
    twist: Any
    wrench: Any


@dataclass
class sensor_msgs__msg__MagneticField:
    """Class for sensor_msgs/msg/MagneticField."""

    header: Any
    magnetic_field: Any
    magnetic_field_covariance: Any


@dataclass
class sensor_msgs__msg__JointState:
    """Class for sensor_msgs/msg/JointState."""

    header: Any
    name: Any
    position: Any
    velocity: Any
    effort: Any


@dataclass
class sensor_msgs__msg__PointField:
    """Class for sensor_msgs/msg/PointField."""

    name: Any
    offset: Any
    datatype: Any
    count: Any


@dataclass
class sensor_msgs__msg__PointCloud2:
    """Class for sensor_msgs/msg/PointCloud2."""

    header: Any
    height: Any
    width: Any
    fields: Any
    is_bigendian: Any
    point_step: Any
    row_step: Any
    data: Any
    is_dense: Any


@dataclass
class sensor_msgs__msg__JoyFeedback:
    """Class for sensor_msgs/msg/JoyFeedback."""

    type: Any
    id: Any
    intensity: Any


@dataclass
class shape_msgs__msg__SolidPrimitive:
    """Class for shape_msgs/msg/SolidPrimitive."""

    type: Any
    dimensions: Any


@dataclass
class shape_msgs__msg__Mesh:
    """Class for shape_msgs/msg/Mesh."""

    triangles: Any
    vertices: Any


@dataclass
class shape_msgs__msg__Plane:
    """Class for shape_msgs/msg/Plane."""

    coef: Any


@dataclass
class shape_msgs__msg__MeshTriangle:
    """Class for shape_msgs/msg/MeshTriangle."""

    vertex_indices: Any


@dataclass
class statistics_msgs__msg__StatisticDataType:
    """Class for statistics_msgs/msg/StatisticDataType."""

    structure_needs_at_least_one_member: Any


@dataclass
class statistics_msgs__msg__StatisticDataPoint:
    """Class for statistics_msgs/msg/StatisticDataPoint."""

    data_type: Any
    data: Any


@dataclass
class statistics_msgs__msg__MetricsMessage:
    """Class for statistics_msgs/msg/MetricsMessage."""

    measurement_source_name: Any
    metrics_source: Any
    unit: Any
    window_start: Any
    window_stop: Any
    statistics: Any


@dataclass
class std_msgs__msg__UInt8:
    """Class for std_msgs/msg/UInt8."""

    data: Any


@dataclass
class std_msgs__msg__Float32MultiArray:
    """Class for std_msgs/msg/Float32MultiArray."""

    layout: Any
    data: Any


@dataclass
class std_msgs__msg__Int8:
    """Class for std_msgs/msg/Int8."""

    data: Any


@dataclass
class std_msgs__msg__Empty:
    """Class for std_msgs/msg/Empty."""

    structure_needs_at_least_one_member: Any


@dataclass
class std_msgs__msg__String:
    """Class for std_msgs/msg/String."""

    data: Any


@dataclass
class std_msgs__msg__MultiArrayDimension:
    """Class for std_msgs/msg/MultiArrayDimension."""

    label: Any
    size: Any
    stride: Any


@dataclass
class std_msgs__msg__UInt64:
    """Class for std_msgs/msg/UInt64."""

    data: Any


@dataclass
class std_msgs__msg__UInt16:
    """Class for std_msgs/msg/UInt16."""

    data: Any


@dataclass
class std_msgs__msg__Float32:
    """Class for std_msgs/msg/Float32."""

    data: Any


@dataclass
class std_msgs__msg__Int64:
    """Class for std_msgs/msg/Int64."""

    data: Any


@dataclass
class std_msgs__msg__Int16MultiArray:
    """Class for std_msgs/msg/Int16MultiArray."""

    layout: Any
    data: Any


@dataclass
class std_msgs__msg__Int16:
    """Class for std_msgs/msg/Int16."""

    data: Any


@dataclass
class std_msgs__msg__Float64MultiArray:
    """Class for std_msgs/msg/Float64MultiArray."""

    layout: Any
    data: Any


@dataclass
class std_msgs__msg__MultiArrayLayout:
    """Class for std_msgs/msg/MultiArrayLayout."""

    dim: Any
    data_offset: Any


@dataclass
class std_msgs__msg__UInt32MultiArray:
    """Class for std_msgs/msg/UInt32MultiArray."""

    layout: Any
    data: Any


@dataclass
class std_msgs__msg__Header:
    """Class for std_msgs/msg/Header."""

    stamp: Any
    frame_id: Any


@dataclass
class std_msgs__msg__ByteMultiArray:
    """Class for std_msgs/msg/ByteMultiArray."""

    layout: Any
    data: Any


@dataclass
class std_msgs__msg__Int8MultiArray:
    """Class for std_msgs/msg/Int8MultiArray."""

    layout: Any
    data: Any


@dataclass
class std_msgs__msg__Float64:
    """Class for std_msgs/msg/Float64."""

    data: Any


@dataclass
class std_msgs__msg__UInt8MultiArray:
    """Class for std_msgs/msg/UInt8MultiArray."""

    layout: Any
    data: Any


@dataclass
class std_msgs__msg__Byte:
    """Class for std_msgs/msg/Byte."""

    data: Any


@dataclass
class std_msgs__msg__Char:
    """Class for std_msgs/msg/Char."""

    data: Any


@dataclass
class std_msgs__msg__UInt64MultiArray:
    """Class for std_msgs/msg/UInt64MultiArray."""

    layout: Any
    data: Any


@dataclass
class std_msgs__msg__Int32MultiArray:
    """Class for std_msgs/msg/Int32MultiArray."""

    layout: Any
    data: Any


@dataclass
class std_msgs__msg__ColorRGBA:
    """Class for std_msgs/msg/ColorRGBA."""

    r: Any
    g: Any
    b: Any
    a: Any


@dataclass
class std_msgs__msg__Bool:
    """Class for std_msgs/msg/Bool."""

    data: Any


@dataclass
class std_msgs__msg__UInt32:
    """Class for std_msgs/msg/UInt32."""

    data: Any


@dataclass
class std_msgs__msg__Int64MultiArray:
    """Class for std_msgs/msg/Int64MultiArray."""

    layout: Any
    data: Any


@dataclass
class std_msgs__msg__Int32:
    """Class for std_msgs/msg/Int32."""

    data: Any


@dataclass
class std_msgs__msg__UInt16MultiArray:
    """Class for std_msgs/msg/UInt16MultiArray."""

    layout: Any
    data: Any


@dataclass
class stereo_msgs__msg__DisparityImage:
    """Class for stereo_msgs/msg/DisparityImage."""

    header: Any
    image: Any
    f: Any
    t: Any
    valid_window: Any
    min_disparity: Any
    max_disparity: Any
    delta_d: Any


@dataclass
class tf2_msgs__msg__TF2Error:
    """Class for tf2_msgs/msg/TF2Error."""

    error: Any
    error_string: Any


@dataclass
class tf2_msgs__msg__TFMessage:
    """Class for tf2_msgs/msg/TFMessage."""

    transforms: Any


@dataclass
class trajectory_msgs__msg__MultiDOFJointTrajectory:
    """Class for trajectory_msgs/msg/MultiDOFJointTrajectory."""

    header: Any
    joint_names: Any
    points: Any


@dataclass
class trajectory_msgs__msg__JointTrajectory:
    """Class for trajectory_msgs/msg/JointTrajectory."""

    header: Any
    joint_names: Any
    points: Any


@dataclass
class trajectory_msgs__msg__JointTrajectoryPoint:
    """Class for trajectory_msgs/msg/JointTrajectoryPoint."""

    positions: Any
    velocities: Any
    accelerations: Any
    effort: Any
    time_from_start: Any


@dataclass
class trajectory_msgs__msg__MultiDOFJointTrajectoryPoint:
    """Class for trajectory_msgs/msg/MultiDOFJointTrajectoryPoint."""

    transforms: Any
    velocities: Any
    accelerations: Any
    time_from_start: Any


@dataclass
class unique_identifier_msgs__msg__UUID:
    """Class for unique_identifier_msgs/msg/UUID."""

    uuid: Any


@dataclass
class visualization_msgs__msg__Marker:
    """Class for visualization_msgs/msg/Marker."""

    header: Any
    ns: Any
    id: Any
    type: Any
    action: Any
    pose: Any
    scale: Any
    color: Any
    lifetime: Any
    frame_locked: Any
    points: Any
    colors: Any
    text: Any
    mesh_resource: Any
    mesh_use_embedded_materials: Any


@dataclass
class visualization_msgs__msg__InteractiveMarkerInit:
    """Class for visualization_msgs/msg/InteractiveMarkerInit."""

    server_id: Any
    seq_num: Any
    markers: Any


@dataclass
class visualization_msgs__msg__MenuEntry:
    """Class for visualization_msgs/msg/MenuEntry."""

    id: Any
    parent_id: Any
    title: Any
    command: Any
    command_type: Any


@dataclass
class visualization_msgs__msg__MarkerArray:
    """Class for visualization_msgs/msg/MarkerArray."""

    markers: Any


@dataclass
class visualization_msgs__msg__InteractiveMarkerUpdate:
    """Class for visualization_msgs/msg/InteractiveMarkerUpdate."""

    server_id: Any
    seq_num: Any
    type: Any
    markers: Any
    poses: Any
    erases: Any


@dataclass
class visualization_msgs__msg__InteractiveMarker:
    """Class for visualization_msgs/msg/InteractiveMarker."""

    header: Any
    pose: Any
    name: Any
    description: Any
    scale: Any
    menu_entries: Any
    controls: Any


@dataclass
class visualization_msgs__msg__InteractiveMarkerFeedback:
    """Class for visualization_msgs/msg/InteractiveMarkerFeedback."""

    header: Any
    client_id: Any
    marker_name: Any
    control_name: Any
    event_type: Any
    pose: Any
    menu_entry_id: Any
    mouse_point: Any
    mouse_point_valid: Any


@dataclass
class visualization_msgs__msg__ImageMarker:
    """Class for visualization_msgs/msg/ImageMarker."""

    header: Any
    ns: Any
    id: Any
    type: Any
    action: Any
    position: Any
    scale: Any
    outline_color: Any
    filled: Any
    fill_color: Any
    lifetime: Any
    points: Any
    outline_colors: Any


@dataclass
class visualization_msgs__msg__InteractiveMarkerControl:
    """Class for visualization_msgs/msg/InteractiveMarkerControl."""

    name: Any
    orientation: Any
    orientation_mode: Any
    interaction_mode: Any
    always_visible: Any
    markers: Any
    independent_marker_orientation: Any
    description: Any


@dataclass
class visualization_msgs__msg__InteractiveMarkerPose:
    """Class for visualization_msgs/msg/InteractiveMarkerPose."""

    header: Any
    pose: Any
    name: Any


@dataclass
class autoware_auto_msgs__msg__BoundingBox:
    """Class for autoware_auto_msgs/msg/BoundingBox."""

    centroid: Any
    size: Any
    orientation: Any
    velocity: Any
    heading: Any
    heading_rate: Any
    corners: Any
    variance: Any
    value: Any
    vehicle_label: Any
    signal_label: Any
    class_likelihood: Any


@dataclass
class autoware_auto_msgs__msg__HADMapBin:
    """Class for autoware_auto_msgs/msg/HADMapBin."""

    header: Any
    map_format: Any
    format_version: Any
    map_version: Any
    data: Any


@dataclass
class autoware_auto_msgs__msg__Quaternion32:
    """Class for autoware_auto_msgs/msg/Quaternion32."""

    x: Any
    y: Any
    z: Any
    w: Any


@dataclass
class autoware_auto_msgs__msg__Trajectory:
    """Class for autoware_auto_msgs/msg/Trajectory."""

    header: Any
    points: Any


@dataclass
class autoware_auto_msgs__msg__Route:
    """Class for autoware_auto_msgs/msg/Route."""

    header: Any
    start_point: Any
    goal_point: Any
    primitives: Any


@dataclass
class autoware_auto_msgs__msg__MapPrimitive:
    """Class for autoware_auto_msgs/msg/MapPrimitive."""

    id: Any
    primitive_type: Any


@dataclass
class autoware_auto_msgs__msg__TrajectoryPoint:
    """Class for autoware_auto_msgs/msg/TrajectoryPoint."""

    time_from_start: Any
    x: Any
    y: Any
    heading: Any
    longitudinal_velocity_mps: Any
    lateral_velocity_mps: Any
    acceleration_mps2: Any
    heading_rate_rps: Any
    front_wheel_angle_rad: Any
    rear_wheel_angle_rad: Any


@dataclass
class autoware_auto_msgs__msg__Complex32:
    """Class for autoware_auto_msgs/msg/Complex32."""

    real: Any
    imag: Any


@dataclass
class autoware_auto_msgs__msg__VehicleOdometry:
    """Class for autoware_auto_msgs/msg/VehicleOdometry."""

    stamp: Any
    velocity_mps: Any
    front_wheel_angle_rad: Any
    rear_wheel_angle_rad: Any


@dataclass
class autoware_auto_msgs__msg__DiagnosticHeader:
    """Class for autoware_auto_msgs/msg/DiagnosticHeader."""

    name: Any
    data_stamp: Any
    computation_start: Any
    runtime: Any
    iterations: Any


@dataclass
class autoware_auto_msgs__msg__HighLevelControlCommand:
    """Class for autoware_auto_msgs/msg/HighLevelControlCommand."""

    stamp: Any
    velocity_mps: Any
    curvature: Any


@dataclass
class autoware_auto_msgs__msg__VehicleStateCommand:
    """Class for autoware_auto_msgs/msg/VehicleStateCommand."""

    stamp: Any
    blinker: Any
    headlight: Any
    wiper: Any
    gear: Any
    mode: Any
    hand_brake: Any
    horn: Any


@dataclass
class autoware_auto_msgs__msg__PointClusters:
    """Class for autoware_auto_msgs/msg/PointClusters."""

    clusters: Any


@dataclass
class autoware_auto_msgs__msg__RawControlCommand:
    """Class for autoware_auto_msgs/msg/RawControlCommand."""

    stamp: Any
    throttle: Any
    brake: Any
    front_steer: Any
    rear_steer: Any


@dataclass
class autoware_auto_msgs__msg__VehicleStateReport:
    """Class for autoware_auto_msgs/msg/VehicleStateReport."""

    stamp: Any
    fuel: Any
    blinker: Any
    headlight: Any
    wiper: Any
    gear: Any
    mode: Any
    hand_brake: Any
    horn: Any


@dataclass
class autoware_auto_msgs__msg__ControlDiagnostic:
    """Class for autoware_auto_msgs/msg/ControlDiagnostic."""

    diag_header: Any
    new_trajectory: Any
    trajectory_source: Any
    pose_source: Any
    lateral_error_m: Any
    longitudinal_error_m: Any
    velocity_error_mps: Any
    acceleration_error_mps2: Any
    yaw_error_rad: Any
    yaw_rate_error_rps: Any


@dataclass
class autoware_auto_msgs__msg__VehicleKinematicState:
    """Class for autoware_auto_msgs/msg/VehicleKinematicState."""

    header: Any
    state: Any
    delta: Any


@dataclass
class autoware_auto_msgs__msg__BoundingBoxArray:
    """Class for autoware_auto_msgs/msg/BoundingBoxArray."""

    header: Any
    boxes: Any


@dataclass
class autoware_auto_msgs__msg__VehicleControlCommand:
    """Class for autoware_auto_msgs/msg/VehicleControlCommand."""

    stamp: Any
    long_accel_mps2: Any
    velocity_mps: Any
    front_wheel_angle_rad: Any
    rear_wheel_angle_rad: Any


@dataclass
class automotive_navigation_msgs__msg__CommandWithHandshake:
    """Class for automotive_navigation_msgs/msg/CommandWithHandshake."""

    header: Any
    msg_counter: Any
    command: Any


@dataclass
class automotive_navigation_msgs__msg__DesiredDestination:
    """Class for automotive_navigation_msgs/msg/DesiredDestination."""

    header: Any
    msg_counter: Any
    valid: Any
    latitude: Any
    longitude: Any


@dataclass
class automotive_navigation_msgs__msg__Direction:
    """Class for automotive_navigation_msgs/msg/Direction."""

    header: Any
    direction: Any


@dataclass
class automotive_navigation_msgs__msg__DistanceToDestination:
    """Class for automotive_navigation_msgs/msg/DistanceToDestination."""

    header: Any
    msg_counter: Any
    distance: Any


@dataclass
class automotive_navigation_msgs__msg__LaneBoundary:
    """Class for automotive_navigation_msgs/msg/LaneBoundary."""

    style: Any
    color: Any
    line: Any


@dataclass
class automotive_navigation_msgs__msg__LaneBoundaryArray:
    """Class for automotive_navigation_msgs/msg/LaneBoundaryArray."""

    boundaries: Any


@dataclass
class automotive_navigation_msgs__msg__ModuleState:
    """Class for automotive_navigation_msgs/msg/ModuleState."""

    header: Any
    name: Any
    state: Any
    info: Any


@dataclass
class automotive_navigation_msgs__msg__PointOfInterest:
    """Class for automotive_navigation_msgs/msg/PointOfInterest."""

    guid: Any
    latitude: Any
    longitude: Any
    params: Any


@dataclass
class automotive_navigation_msgs__msg__PointOfInterestArray:
    """Class for automotive_navigation_msgs/msg/PointOfInterestArray."""

    header: Any
    update_num: Any
    point_list: Any


@dataclass
class automotive_navigation_msgs__msg__PointOfInterestRequest:
    """Class for automotive_navigation_msgs/msg/PointOfInterestRequest."""

    header: Any
    name: Any
    module_name: Any
    request_id: Any
    cancel: Any
    update_num: Any
    guid_valid: Any
    guid: Any
    tolerance: Any


@dataclass
class automotive_navigation_msgs__msg__PointOfInterestResponse:
    """Class for automotive_navigation_msgs/msg/PointOfInterestResponse."""

    header: Any
    name: Any
    module_name: Any
    request_id: Any
    update_num: Any
    point_statuses: Any


@dataclass
class automotive_navigation_msgs__msg__PointOfInterestStatus:
    """Class for automotive_navigation_msgs/msg/PointOfInterestStatus."""

    guid: Any
    distance: Any
    heading: Any
    x_position: Any
    y_position: Any
    params: Any


@dataclass
class automotive_navigation_msgs__msg__RoadNetworkBoundaries:
    """Class for automotive_navigation_msgs/msg/RoadNetworkBoundaries."""

    header: Any
    road_network_boundaries: Any


@dataclass
class automotive_platform_msgs__msg__AdaptiveCruiseControlCommand:
    """Class for automotive_platform_msgs/msg/AdaptiveCruiseControlCommand."""

    header: Any
    msg_counter: Any
    set_speed: Any
    set: Any
    resume: Any
    cancel: Any
    speed_up: Any
    slow_down: Any
    further: Any
    closer: Any


@dataclass
class automotive_platform_msgs__msg__AdaptiveCruiseControlSettings:
    """Class for automotive_platform_msgs/msg/AdaptiveCruiseControlSettings."""

    header: Any
    set_speed: Any
    following_spot: Any
    min_percent: Any
    step_percent: Any
    cipv_percent: Any
    max_distance: Any


@dataclass
class automotive_platform_msgs__msg__BlindSpotIndicators:
    """Class for automotive_platform_msgs/msg/BlindSpotIndicators."""

    header: Any
    left: Any
    right: Any


@dataclass
class automotive_platform_msgs__msg__BrakeCommand:
    """Class for automotive_platform_msgs/msg/BrakeCommand."""

    header: Any
    brake_pedal: Any


@dataclass
class automotive_platform_msgs__msg__BrakeFeedback:
    """Class for automotive_platform_msgs/msg/BrakeFeedback."""

    header: Any
    brake_pedal: Any


@dataclass
class automotive_platform_msgs__msg__CabinReport:
    """Class for automotive_platform_msgs/msg/CabinReport."""

    header: Any
    door_open_front_right: Any
    door_open_front_left: Any
    door_open_rear_right: Any
    door_open_rear_left: Any
    hood_open: Any
    trunk_open: Any
    passenger_present: Any
    passenger_airbag_enabled: Any
    seatbelt_engaged_driver: Any
    seatbelt_engaged_passenger: Any


@dataclass
class automotive_platform_msgs__msg__CurvatureFeedback:
    """Class for automotive_platform_msgs/msg/CurvatureFeedback."""

    header: Any
    curvature: Any


@dataclass
class automotive_platform_msgs__msg__DriverCommands:
    """Class for automotive_platform_msgs/msg/DriverCommands."""

    msg_counter: Any
    engage: Any
    disengage: Any
    speed_up: Any
    slow_down: Any
    further: Any
    closer: Any
    right_turn: Any
    left_turn: Any


@dataclass
class automotive_platform_msgs__msg__Gear:
    """Class for automotive_platform_msgs/msg/Gear."""

    gear: Any


@dataclass
class automotive_platform_msgs__msg__GearCommand:
    """Class for automotive_platform_msgs/msg/GearCommand."""

    header: Any
    command: Any


@dataclass
class automotive_platform_msgs__msg__GearFeedback:
    """Class for automotive_platform_msgs/msg/GearFeedback."""

    header: Any
    current_gear: Any


@dataclass
class automotive_platform_msgs__msg__HillStartAssist:
    """Class for automotive_platform_msgs/msg/HillStartAssist."""

    header: Any
    active: Any


@dataclass
class automotive_platform_msgs__msg__Speed:
    """Class for automotive_platform_msgs/msg/Speed."""

    header: Any
    module_name: Any
    speed: Any
    acceleration_limit: Any
    deceleration_limit: Any


@dataclass
class automotive_platform_msgs__msg__SpeedMode:
    """Class for automotive_platform_msgs/msg/SpeedMode."""

    header: Any
    mode: Any
    speed: Any
    acceleration_limit: Any
    deceleration_limit: Any


@dataclass
class automotive_platform_msgs__msg__SpeedPedals:
    """Class for automotive_platform_msgs/msg/SpeedPedals."""

    header: Any
    mode: Any
    throttle: Any
    brake: Any


@dataclass
class automotive_platform_msgs__msg__Steer:
    """Class for automotive_platform_msgs/msg/Steer."""

    header: Any
    module_name: Any
    curvature: Any
    max_curvature_rate: Any


@dataclass
class automotive_platform_msgs__msg__SteerMode:
    """Class for automotive_platform_msgs/msg/SteerMode."""

    header: Any
    mode: Any
    curvature: Any
    max_curvature_rate: Any


@dataclass
class automotive_platform_msgs__msg__SteerWheel:
    """Class for automotive_platform_msgs/msg/SteerWheel."""

    header: Any
    mode: Any
    angle: Any
    angle_velocity: Any


@dataclass
class automotive_platform_msgs__msg__SteeringCommand:
    """Class for automotive_platform_msgs/msg/SteeringCommand."""

    header: Any
    steering_wheel_angle: Any


@dataclass
class automotive_platform_msgs__msg__SteeringFeedback:
    """Class for automotive_platform_msgs/msg/SteeringFeedback."""

    header: Any
    steering_wheel_angle: Any


@dataclass
class automotive_platform_msgs__msg__ThrottleCommand:
    """Class for automotive_platform_msgs/msg/ThrottleCommand."""

    header: Any
    throttle_pedal: Any


@dataclass
class automotive_platform_msgs__msg__ThrottleFeedback:
    """Class for automotive_platform_msgs/msg/ThrottleFeedback."""

    header: Any
    throttle_pedal: Any


@dataclass
class automotive_platform_msgs__msg__TurnSignalCommand:
    """Class for automotive_platform_msgs/msg/TurnSignalCommand."""

    header: Any
    mode: Any
    turn_signal: Any


@dataclass
class automotive_platform_msgs__msg__UserInputADAS:
    """Class for automotive_platform_msgs/msg/UserInputADAS."""

    header: Any
    btn_cc_on: Any
    btn_cc_off: Any
    btn_cc_on_off: Any
    btn_cc_set_inc: Any
    btn_cc_set_dec: Any
    btn_cc_res: Any
    btn_cc_cncl: Any
    btn_cc_res_cncl: Any
    btn_acc_gap_inc: Any
    btn_acc_gap_dec: Any
    btn_lka_on: Any
    btn_lka_off: Any
    btn_lka_on_off: Any


@dataclass
class automotive_platform_msgs__msg__UserInputMedia:
    """Class for automotive_platform_msgs/msg/UserInputMedia."""

    header: Any
    btn_vol_up: Any
    btn_vol_down: Any
    btn_mute: Any
    btn_next: Any
    btn_prev: Any
    btn_next_hang_up: Any
    btn_prev_answer: Any
    btn_hang_up: Any
    btn_answer: Any
    btn_play: Any
    btn_pause: Any
    btn_play_pause: Any
    btn_mode: Any


@dataclass
class automotive_platform_msgs__msg__UserInputMenus:
    """Class for automotive_platform_msgs/msg/UserInputMenus."""

    header: Any
    str_whl_left_btn_left: Any
    str_whl_left_btn_down: Any
    str_whl_left_btn_right: Any
    str_whl_left_btn_up: Any
    str_whl_left_btn_ok: Any
    str_whl_right_btn_left: Any
    str_whl_right_btn_down: Any
    str_whl_right_btn_right: Any
    str_whl_right_btn_up: Any
    str_whl_right_btn_ok: Any
    cntr_cons_btn_left: Any
    cntr_cons_btn_down: Any
    cntr_cons_btn_right: Any
    cntr_cons_btn_up: Any
    cntr_cons_btn_ok: Any


@dataclass
class automotive_platform_msgs__msg__VelocityAccel:
    """Class for automotive_platform_msgs/msg/VelocityAccel."""

    header: Any
    velocity: Any
    accleration: Any


@dataclass
class automotive_platform_msgs__msg__VelocityAccelCov:
    """Class for automotive_platform_msgs/msg/VelocityAccelCov."""

    header: Any
    velocity: Any
    accleration: Any
    covariance: Any


FIELDDEFS = {
    'builtin_interfaces/msg/Time': [
        ('sec', [1, 'int32']),
        ('nanosec', [1, 'uint32']),
    ],
    'builtin_interfaces/msg/Duration': [
        ('sec', [1, 'int32']),
        ('nanosec', [1, 'uint32']),
    ],
    'diagnostic_msgs/msg/DiagnosticStatus': [
        ('level', [1, 'uint8']),
        ('name', [1, 'string']),
        ('message', [1, 'string']),
        ('hardware_id', [1, 'string']),
        ('values', [4, [2, 'diagnostic_msgs/msg/KeyValue']]),
    ],
    'diagnostic_msgs/msg/DiagnosticArray': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('status', [4, [2, 'diagnostic_msgs/msg/DiagnosticStatus']]),
    ],
    'diagnostic_msgs/msg/KeyValue': [
        ('key', [1, 'string']),
        ('value', [1, 'string']),
    ],
    'geometry_msgs/msg/AccelWithCovariance': [
        ('accel', [2, 'geometry_msgs/msg/Accel']),
        ('covariance', [3, 36, [1, 'float64']]),
    ],
    'geometry_msgs/msg/Point32': [
        ('x', [1, 'float32']),
        ('y', [1, 'float32']),
        ('z', [1, 'float32']),
    ],
    'geometry_msgs/msg/Vector3': [
        ('x', [1, 'float64']),
        ('y', [1, 'float64']),
        ('z', [1, 'float64']),
    ],
    'geometry_msgs/msg/Inertia': [
        ('m', [1, 'float64']),
        ('com', [2, 'geometry_msgs/msg/Vector3']),
        ('ixx', [1, 'float64']),
        ('ixy', [1, 'float64']),
        ('ixz', [1, 'float64']),
        ('iyy', [1, 'float64']),
        ('iyz', [1, 'float64']),
        ('izz', [1, 'float64']),
    ],
    'geometry_msgs/msg/PoseWithCovarianceStamped': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('pose', [2, 'geometry_msgs/msg/PoseWithCovariance']),
    ],
    'geometry_msgs/msg/Twist': [
        ('linear', [2, 'geometry_msgs/msg/Vector3']),
        ('angular', [2, 'geometry_msgs/msg/Vector3']),
    ],
    'geometry_msgs/msg/Pose': [
        ('position', [2, 'geometry_msgs/msg/Point']),
        ('orientation', [2, 'geometry_msgs/msg/Quaternion']),
    ],
    'geometry_msgs/msg/Point': [
        ('x', [1, 'float64']),
        ('y', [1, 'float64']),
        ('z', [1, 'float64']),
    ],
    'geometry_msgs/msg/Vector3Stamped': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('vector', [2, 'geometry_msgs/msg/Vector3']),
    ],
    'geometry_msgs/msg/Transform': [
        ('translation', [2, 'geometry_msgs/msg/Vector3']),
        ('rotation', [2, 'geometry_msgs/msg/Quaternion']),
    ],
    'geometry_msgs/msg/PolygonStamped': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('polygon', [2, 'geometry_msgs/msg/Polygon']),
    ],
    'geometry_msgs/msg/Quaternion': [
        ('x', [1, 'float64']),
        ('y', [1, 'float64']),
        ('z', [1, 'float64']),
        ('w', [1, 'float64']),
    ],
    'geometry_msgs/msg/Pose2D': [
        ('x', [1, 'float64']),
        ('y', [1, 'float64']),
        ('theta', [1, 'float64']),
    ],
    'geometry_msgs/msg/InertiaStamped': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('inertia', [2, 'geometry_msgs/msg/Inertia']),
    ],
    'geometry_msgs/msg/TwistStamped': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('twist', [2, 'geometry_msgs/msg/Twist']),
    ],
    'geometry_msgs/msg/PoseStamped': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('pose', [2, 'geometry_msgs/msg/Pose']),
    ],
    'geometry_msgs/msg/PointStamped': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('point', [2, 'geometry_msgs/msg/Point']),
    ],
    'geometry_msgs/msg/Polygon': [
        ('points', [4, [2, 'geometry_msgs/msg/Point32']]),
    ],
    'geometry_msgs/msg/PoseArray': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('poses', [4, [2, 'geometry_msgs/msg/Pose']]),
    ],
    'geometry_msgs/msg/AccelStamped': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('accel', [2, 'geometry_msgs/msg/Accel']),
    ],
    'geometry_msgs/msg/TwistWithCovarianceStamped': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('twist', [2, 'geometry_msgs/msg/TwistWithCovariance']),
    ],
    'geometry_msgs/msg/QuaternionStamped': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('quaternion', [2, 'geometry_msgs/msg/Quaternion']),
    ],
    'geometry_msgs/msg/WrenchStamped': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('wrench', [2, 'geometry_msgs/msg/Wrench']),
    ],
    'geometry_msgs/msg/AccelWithCovarianceStamped': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('accel', [2, 'geometry_msgs/msg/AccelWithCovariance']),
    ],
    'geometry_msgs/msg/PoseWithCovariance': [
        ('pose', [2, 'geometry_msgs/msg/Pose']),
        ('covariance', [3, 36, [1, 'float64']]),
    ],
    'geometry_msgs/msg/Wrench': [
        ('force', [2, 'geometry_msgs/msg/Vector3']),
        ('torque', [2, 'geometry_msgs/msg/Vector3']),
    ],
    'geometry_msgs/msg/TransformStamped': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('child_frame_id', [1, 'string']),
        ('transform', [2, 'geometry_msgs/msg/Transform']),
    ],
    'geometry_msgs/msg/Accel': [
        ('linear', [2, 'geometry_msgs/msg/Vector3']),
        ('angular', [2, 'geometry_msgs/msg/Vector3']),
    ],
    'geometry_msgs/msg/TwistWithCovariance': [
        ('twist', [2, 'geometry_msgs/msg/Twist']),
        ('covariance', [3, 36, [1, 'float64']]),
    ],
    'libstatistics_collector/msg/DummyMessage': [
        ('header', [2, 'std_msgs/msg/Header']),
    ],
    'lifecycle_msgs/msg/TransitionDescription': [
        ('transition', [2, 'lifecycle_msgs/msg/Transition']),
        ('start_state', [2, 'lifecycle_msgs/msg/State']),
        ('goal_state', [2, 'lifecycle_msgs/msg/State']),
    ],
    'lifecycle_msgs/msg/State': [
        ('id', [1, 'uint8']),
        ('label', [1, 'string']),
    ],
    'lifecycle_msgs/msg/TransitionEvent': [
        ('timestamp', [1, 'uint64']),
        ('transition', [2, 'lifecycle_msgs/msg/Transition']),
        ('start_state', [2, 'lifecycle_msgs/msg/State']),
        ('goal_state', [2, 'lifecycle_msgs/msg/State']),
    ],
    'lifecycle_msgs/msg/Transition': [
        ('id', [1, 'uint8']),
        ('label', [1, 'string']),
    ],
    'nav_msgs/msg/MapMetaData': [
        ('map_load_time', [2, 'builtin_interfaces/msg/Time']),
        ('resolution', [1, 'float32']),
        ('width', [1, 'uint32']),
        ('height', [1, 'uint32']),
        ('origin', [2, 'geometry_msgs/msg/Pose']),
    ],
    'nav_msgs/msg/GridCells': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('cell_width', [1, 'float32']),
        ('cell_height', [1, 'float32']),
        ('cells', [4, [2, 'geometry_msgs/msg/Point']]),
    ],
    'nav_msgs/msg/Odometry': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('child_frame_id', [1, 'string']),
        ('pose', [2, 'geometry_msgs/msg/PoseWithCovariance']),
        ('twist', [2, 'geometry_msgs/msg/TwistWithCovariance']),
    ],
    'nav_msgs/msg/Path': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('poses', [4, [2, 'geometry_msgs/msg/PoseStamped']]),
    ],
    'nav_msgs/msg/OccupancyGrid': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('info', [2, 'nav_msgs/msg/MapMetaData']),
        ('data', [4, [1, 'int8']]),
    ],
    'rcl_interfaces/msg/ListParametersResult': [
        ('names', [4, [1, 'string']]),
        ('prefixes', [4, [1, 'string']]),
    ],
    'rcl_interfaces/msg/ParameterType': [
        ('structure_needs_at_least_one_member', [1, 'uint8']),
    ],
    'rcl_interfaces/msg/ParameterEventDescriptors': [
        ('new_parameters', [4, [2, 'rcl_interfaces/msg/ParameterDescriptor']]),
        ('changed_parameters', [4, [2, 'rcl_interfaces/msg/ParameterDescriptor']]),
        ('deleted_parameters', [4, [2, 'rcl_interfaces/msg/ParameterDescriptor']]),
    ],
    'rcl_interfaces/msg/ParameterEvent': [
        ('stamp', [2, 'builtin_interfaces/msg/Time']),
        ('node', [1, 'string']),
        ('new_parameters', [4, [2, 'rcl_interfaces/msg/Parameter']]),
        ('changed_parameters', [4, [2, 'rcl_interfaces/msg/Parameter']]),
        ('deleted_parameters', [4, [2, 'rcl_interfaces/msg/Parameter']]),
    ],
    'rcl_interfaces/msg/IntegerRange': [
        ('from_value', [1, 'int64']),
        ('to_value', [1, 'int64']),
        ('step', [1, 'uint64']),
    ],
    'rcl_interfaces/msg/Parameter': [
        ('name', [1, 'string']),
        ('value', [2, 'rcl_interfaces/msg/ParameterValue']),
    ],
    'rcl_interfaces/msg/ParameterValue': [
        ('type', [1, 'uint8']),
        ('bool_value', [1, 'bool']),
        ('integer_value', [1, 'int64']),
        ('double_value', [1, 'float64']),
        ('string_value', [1, 'string']),
        ('byte_array_value', [4, [1, 'uint8']]),
        ('bool_array_value', [4, [1, 'bool']]),
        ('integer_array_value', [4, [1, 'int64']]),
        ('double_array_value', [4, [1, 'float64']]),
        ('string_array_value', [4, [1, 'string']]),
    ],
    'rcl_interfaces/msg/FloatingPointRange': [
        ('from_value', [1, 'float64']),
        ('to_value', [1, 'float64']),
        ('step', [1, 'float64']),
    ],
    'rcl_interfaces/msg/SetParametersResult': [
        ('successful', [1, 'bool']),
        ('reason', [1, 'string']),
    ],
    'rcl_interfaces/msg/Log': [
        ('stamp', [2, 'builtin_interfaces/msg/Time']),
        ('level', [1, 'uint8']),
        ('name', [1, 'string']),
        ('msg', [1, 'string']),
        ('file', [1, 'string']),
        ('function', [1, 'string']),
        ('line', [1, 'uint32']),
    ],
    'rcl_interfaces/msg/ParameterDescriptor': [
        ('name', [1, 'string']),
        ('type', [1, 'uint8']),
        ('description', [1, 'string']),
        ('additional_constraints', [1, 'string']),
        ('read_only', [1, 'bool']),
        ('floating_point_range', [4, [2, 'rcl_interfaces/msg/FloatingPointRange']]),
        ('integer_range', [4, [2, 'rcl_interfaces/msg/IntegerRange']]),
    ],
    'rmw_dds_common/msg/Gid': [
        ('data', [3, 24, [1, 'uint8']]),
    ],
    'rmw_dds_common/msg/NodeEntitiesInfo': [
        ('node_namespace', [1, 'string', [6, 256]]),
        ('node_name', [1, 'string', [6, 256]]),
        ('reader_gid_seq', [4, [2, 'rmw_dds_common/msg/Gid']]),
        ('writer_gid_seq', [4, [2, 'rmw_dds_common/msg/Gid']]),
    ],
    'rmw_dds_common/msg/ParticipantEntitiesInfo': [
        ('gid', [2, 'rmw_dds_common/msg/Gid']),
        ('node_entities_info_seq', [4, [2, 'rmw_dds_common/msg/NodeEntitiesInfo']]),
    ],
    'rosgraph_msgs/msg/Clock': [
        ('clock', [2, 'builtin_interfaces/msg/Time']),
    ],
    'sensor_msgs/msg/Temperature': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('temperature', [1, 'float64']),
        ('variance', [1, 'float64']),
    ],
    'sensor_msgs/msg/Range': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('radiation_type', [1, 'uint8']),
        ('field_of_view', [1, 'float32']),
        ('min_range', [1, 'float32']),
        ('max_range', [1, 'float32']),
        ('range', [1, 'float32']),
    ],
    'sensor_msgs/msg/RegionOfInterest': [
        ('x_offset', [1, 'uint32']),
        ('y_offset', [1, 'uint32']),
        ('height', [1, 'uint32']),
        ('width', [1, 'uint32']),
        ('do_rectify', [1, 'bool']),
    ],
    'sensor_msgs/msg/JoyFeedbackArray': [
        ('array', [4, [2, 'sensor_msgs/msg/JoyFeedback']]),
    ],
    'sensor_msgs/msg/TimeReference': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('time_ref', [2, 'builtin_interfaces/msg/Time']),
        ('source', [1, 'string']),
    ],
    'sensor_msgs/msg/CompressedImage': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('format', [1, 'string']),
        ('data', [4, [1, 'uint8']]),
    ],
    'sensor_msgs/msg/MultiEchoLaserScan': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('angle_min', [1, 'float32']),
        ('angle_max', [1, 'float32']),
        ('angle_increment', [1, 'float32']),
        ('time_increment', [1, 'float32']),
        ('scan_time', [1, 'float32']),
        ('range_min', [1, 'float32']),
        ('range_max', [1, 'float32']),
        ('ranges', [4, [2, 'sensor_msgs/msg/LaserEcho']]),
        ('intensities', [4, [2, 'sensor_msgs/msg/LaserEcho']]),
    ],
    'sensor_msgs/msg/LaserEcho': [
        ('echoes', [4, [1, 'float32']]),
    ],
    'sensor_msgs/msg/ChannelFloat32': [
        ('name', [1, 'string']),
        ('values', [4, [1, 'float32']]),
    ],
    'sensor_msgs/msg/CameraInfo': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('height', [1, 'uint32']),
        ('width', [1, 'uint32']),
        ('distortion_model', [1, 'string']),
        ('d', [4, [1, 'float64']]),
        ('k', [3, 9, [1, 'float64']]),
        ('r', [3, 9, [1, 'float64']]),
        ('p', [3, 12, [1, 'float64']]),
        ('binning_x', [1, 'uint32']),
        ('binning_y', [1, 'uint32']),
        ('roi', [2, 'sensor_msgs/msg/RegionOfInterest']),
    ],
    'sensor_msgs/msg/RelativeHumidity': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('relative_humidity', [1, 'float64']),
        ('variance', [1, 'float64']),
    ],
    'sensor_msgs/msg/FluidPressure': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('fluid_pressure', [1, 'float64']),
        ('variance', [1, 'float64']),
    ],
    'sensor_msgs/msg/LaserScan': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('angle_min', [1, 'float32']),
        ('angle_max', [1, 'float32']),
        ('angle_increment', [1, 'float32']),
        ('time_increment', [1, 'float32']),
        ('scan_time', [1, 'float32']),
        ('range_min', [1, 'float32']),
        ('range_max', [1, 'float32']),
        ('ranges', [4, [1, 'float32']]),
        ('intensities', [4, [1, 'float32']]),
    ],
    'sensor_msgs/msg/BatteryState': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('voltage', [1, 'float32']),
        ('temperature', [1, 'float32']),
        ('current', [1, 'float32']),
        ('charge', [1, 'float32']),
        ('capacity', [1, 'float32']),
        ('design_capacity', [1, 'float32']),
        ('percentage', [1, 'float32']),
        ('power_supply_status', [1, 'uint8']),
        ('power_supply_health', [1, 'uint8']),
        ('power_supply_technology', [1, 'uint8']),
        ('present', [1, 'bool']),
        ('cell_voltage', [4, [1, 'float32']]),
        ('cell_temperature', [4, [1, 'float32']]),
        ('location', [1, 'string']),
        ('serial_number', [1, 'string']),
    ],
    'sensor_msgs/msg/Image': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('height', [1, 'uint32']),
        ('width', [1, 'uint32']),
        ('encoding', [1, 'string']),
        ('is_bigendian', [1, 'uint8']),
        ('step', [1, 'uint32']),
        ('data', [4, [1, 'uint8']]),
    ],
    'sensor_msgs/msg/PointCloud': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('points', [4, [2, 'geometry_msgs/msg/Point32']]),
        ('channels', [4, [2, 'sensor_msgs/msg/ChannelFloat32']]),
    ],
    'sensor_msgs/msg/Imu': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('orientation', [2, 'geometry_msgs/msg/Quaternion']),
        ('orientation_covariance', [3, 9, [1, 'float64']]),
        ('angular_velocity', [2, 'geometry_msgs/msg/Vector3']),
        ('angular_velocity_covariance', [3, 9, [1, 'float64']]),
        ('linear_acceleration', [2, 'geometry_msgs/msg/Vector3']),
        ('linear_acceleration_covariance', [3, 9, [1, 'float64']]),
    ],
    'sensor_msgs/msg/NavSatStatus': [
        ('status', [1, 'int8']),
        ('service', [1, 'uint16']),
    ],
    'sensor_msgs/msg/Illuminance': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('illuminance', [1, 'float64']),
        ('variance', [1, 'float64']),
    ],
    'sensor_msgs/msg/Joy': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('axes', [4, [1, 'float32']]),
        ('buttons', [4, [1, 'int32']]),
    ],
    'sensor_msgs/msg/NavSatFix': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('status', [2, 'sensor_msgs/msg/NavSatStatus']),
        ('latitude', [1, 'float64']),
        ('longitude', [1, 'float64']),
        ('altitude', [1, 'float64']),
        ('position_covariance', [3, 9, [1, 'float64']]),
        ('position_covariance_type', [1, 'uint8']),
    ],
    'sensor_msgs/msg/MultiDOFJointState': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('joint_names', [4, [1, 'string']]),
        ('transforms', [4, [2, 'geometry_msgs/msg/Transform']]),
        ('twist', [4, [2, 'geometry_msgs/msg/Twist']]),
        ('wrench', [4, [2, 'geometry_msgs/msg/Wrench']]),
    ],
    'sensor_msgs/msg/MagneticField': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('magnetic_field', [2, 'geometry_msgs/msg/Vector3']),
        ('magnetic_field_covariance', [3, 9, [1, 'float64']]),
    ],
    'sensor_msgs/msg/JointState': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('name', [4, [1, 'string']]),
        ('position', [4, [1, 'float64']]),
        ('velocity', [4, [1, 'float64']]),
        ('effort', [4, [1, 'float64']]),
    ],
    'sensor_msgs/msg/PointField': [
        ('name', [1, 'string']),
        ('offset', [1, 'uint32']),
        ('datatype', [1, 'uint8']),
        ('count', [1, 'uint32']),
    ],
    'sensor_msgs/msg/PointCloud2': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('height', [1, 'uint32']),
        ('width', [1, 'uint32']),
        ('fields', [4, [2, 'sensor_msgs/msg/PointField']]),
        ('is_bigendian', [1, 'bool']),
        ('point_step', [1, 'uint32']),
        ('row_step', [1, 'uint32']),
        ('data', [4, [1, 'uint8']]),
        ('is_dense', [1, 'bool']),
    ],
    'sensor_msgs/msg/JoyFeedback': [
        ('type', [1, 'uint8']),
        ('id', [1, 'uint8']),
        ('intensity', [1, 'float32']),
    ],
    'shape_msgs/msg/SolidPrimitive': [
        ('type', [1, 'uint8']),
        ('dimensions', [4, [1, 'float64']]),
    ],
    'shape_msgs/msg/Mesh': [
        ('triangles', [4, [2, 'shape_msgs/msg/MeshTriangle']]),
        ('vertices', [4, [2, 'geometry_msgs/msg/Point']]),
    ],
    'shape_msgs/msg/Plane': [
        ('coef', [3, 4, [1, 'float64']]),
    ],
    'shape_msgs/msg/MeshTriangle': [
        ('vertex_indices', [3, 3, [1, 'uint32']]),
    ],
    'statistics_msgs/msg/StatisticDataType': [
        ('structure_needs_at_least_one_member', [1, 'uint8']),
    ],
    'statistics_msgs/msg/StatisticDataPoint': [
        ('data_type', [1, 'uint8']),
        ('data', [1, 'float64']),
    ],
    'statistics_msgs/msg/MetricsMessage': [
        ('measurement_source_name', [1, 'string']),
        ('metrics_source', [1, 'string']),
        ('unit', [1, 'string']),
        ('window_start', [2, 'builtin_interfaces/msg/Time']),
        ('window_stop', [2, 'builtin_interfaces/msg/Time']),
        ('statistics', [4, [2, 'statistics_msgs/msg/StatisticDataPoint']]),
    ],
    'std_msgs/msg/UInt8': [
        ('data', [1, 'uint8']),
    ],
    'std_msgs/msg/Float32MultiArray': [
        ('layout', [2, 'std_msgs/msg/MultiArrayLayout']),
        ('data', [4, [1, 'float32']]),
    ],
    'std_msgs/msg/Int8': [
        ('data', [1, 'int8']),
    ],
    'std_msgs/msg/Empty': [
        ('structure_needs_at_least_one_member', [1, 'uint8']),
    ],
    'std_msgs/msg/String': [
        ('data', [1, 'string']),
    ],
    'std_msgs/msg/MultiArrayDimension': [
        ('label', [1, 'string']),
        ('size', [1, 'uint32']),
        ('stride', [1, 'uint32']),
    ],
    'std_msgs/msg/UInt64': [
        ('data', [1, 'uint64']),
    ],
    'std_msgs/msg/UInt16': [
        ('data', [1, 'uint16']),
    ],
    'std_msgs/msg/Float32': [
        ('data', [1, 'float32']),
    ],
    'std_msgs/msg/Int64': [
        ('data', [1, 'int64']),
    ],
    'std_msgs/msg/Int16MultiArray': [
        ('layout', [2, 'std_msgs/msg/MultiArrayLayout']),
        ('data', [4, [1, 'int16']]),
    ],
    'std_msgs/msg/Int16': [
        ('data', [1, 'int16']),
    ],
    'std_msgs/msg/Float64MultiArray': [
        ('layout', [2, 'std_msgs/msg/MultiArrayLayout']),
        ('data', [4, [1, 'float64']]),
    ],
    'std_msgs/msg/MultiArrayLayout': [
        ('dim', [4, [2, 'std_msgs/msg/MultiArrayDimension']]),
        ('data_offset', [1, 'uint32']),
    ],
    'std_msgs/msg/UInt32MultiArray': [
        ('layout', [2, 'std_msgs/msg/MultiArrayLayout']),
        ('data', [4, [1, 'uint32']]),
    ],
    'std_msgs/msg/Header': [
        ('stamp', [2, 'builtin_interfaces/msg/Time']),
        ('frame_id', [1, 'string']),
    ],
    'std_msgs/msg/ByteMultiArray': [
        ('layout', [2, 'std_msgs/msg/MultiArrayLayout']),
        ('data', [4, [1, 'uint8']]),
    ],
    'std_msgs/msg/Int8MultiArray': [
        ('layout', [2, 'std_msgs/msg/MultiArrayLayout']),
        ('data', [4, [1, 'int8']]),
    ],
    'std_msgs/msg/Float64': [
        ('data', [1, 'float64']),
    ],
    'std_msgs/msg/UInt8MultiArray': [
        ('layout', [2, 'std_msgs/msg/MultiArrayLayout']),
        ('data', [4, [1, 'uint8']]),
    ],
    'std_msgs/msg/Byte': [
        ('data', [1, 'uint8']),
    ],
    'std_msgs/msg/Char': [
        ('data', [1, 'uint8']),
    ],
    'std_msgs/msg/UInt64MultiArray': [
        ('layout', [2, 'std_msgs/msg/MultiArrayLayout']),
        ('data', [4, [1, 'uint64']]),
    ],
    'std_msgs/msg/Int32MultiArray': [
        ('layout', [2, 'std_msgs/msg/MultiArrayLayout']),
        ('data', [4, [1, 'int32']]),
    ],
    'std_msgs/msg/ColorRGBA': [
        ('r', [1, 'float32']),
        ('g', [1, 'float32']),
        ('b', [1, 'float32']),
        ('a', [1, 'float32']),
    ],
    'std_msgs/msg/Bool': [
        ('data', [1, 'bool']),
    ],
    'std_msgs/msg/UInt32': [
        ('data', [1, 'uint32']),
    ],
    'std_msgs/msg/Int64MultiArray': [
        ('layout', [2, 'std_msgs/msg/MultiArrayLayout']),
        ('data', [4, [1, 'int64']]),
    ],
    'std_msgs/msg/Int32': [
        ('data', [1, 'int32']),
    ],
    'std_msgs/msg/UInt16MultiArray': [
        ('layout', [2, 'std_msgs/msg/MultiArrayLayout']),
        ('data', [4, [1, 'uint16']]),
    ],
    'stereo_msgs/msg/DisparityImage': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('image', [2, 'sensor_msgs/msg/Image']),
        ('f', [1, 'float32']),
        ('t', [1, 'float32']),
        ('valid_window', [2, 'sensor_msgs/msg/RegionOfInterest']),
        ('min_disparity', [1, 'float32']),
        ('max_disparity', [1, 'float32']),
        ('delta_d', [1, 'float32']),
    ],
    'tf2_msgs/msg/TF2Error': [
        ('error', [1, 'uint8']),
        ('error_string', [1, 'string']),
    ],
    'tf2_msgs/msg/TFMessage': [
        ('transforms', [4, [2, 'geometry_msgs/msg/TransformStamped']]),
    ],
    'trajectory_msgs/msg/MultiDOFJointTrajectory': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('joint_names', [4, [1, 'string']]),
        ('points', [4, [2, 'trajectory_msgs/msg/MultiDOFJointTrajectoryPoint']]),
    ],
    'trajectory_msgs/msg/JointTrajectory': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('joint_names', [4, [1, 'string']]),
        ('points', [4, [2, 'trajectory_msgs/msg/JointTrajectoryPoint']]),
    ],
    'trajectory_msgs/msg/JointTrajectoryPoint': [
        ('positions', [4, [1, 'float64']]),
        ('velocities', [4, [1, 'float64']]),
        ('accelerations', [4, [1, 'float64']]),
        ('effort', [4, [1, 'float64']]),
        ('time_from_start', [2, 'builtin_interfaces/msg/Duration']),
    ],
    'trajectory_msgs/msg/MultiDOFJointTrajectoryPoint': [
        ('transforms', [4, [2, 'geometry_msgs/msg/Transform']]),
        ('velocities', [4, [2, 'geometry_msgs/msg/Twist']]),
        ('accelerations', [4, [2, 'geometry_msgs/msg/Twist']]),
        ('time_from_start', [2, 'builtin_interfaces/msg/Duration']),
    ],
    'unique_identifier_msgs/msg/UUID': [
        ('uuid', [3, 16, [1, 'uint8']]),
    ],
    'visualization_msgs/msg/Marker': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('ns', [1, 'string']),
        ('id', [1, 'int32']),
        ('type', [1, 'int32']),
        ('action', [1, 'int32']),
        ('pose', [2, 'geometry_msgs/msg/Pose']),
        ('scale', [2, 'geometry_msgs/msg/Vector3']),
        ('color', [2, 'std_msgs/msg/ColorRGBA']),
        ('lifetime', [2, 'builtin_interfaces/msg/Duration']),
        ('frame_locked', [1, 'bool']),
        ('points', [4, [2, 'geometry_msgs/msg/Point']]),
        ('colors', [4, [2, 'std_msgs/msg/ColorRGBA']]),
        ('text', [1, 'string']),
        ('mesh_resource', [1, 'string']),
        ('mesh_use_embedded_materials', [1, 'bool']),
    ],
    'visualization_msgs/msg/InteractiveMarkerInit': [
        ('server_id', [1, 'string']),
        ('seq_num', [1, 'uint64']),
        ('markers', [4, [2, 'visualization_msgs/msg/InteractiveMarker']]),
    ],
    'visualization_msgs/msg/MenuEntry': [
        ('id', [1, 'uint32']),
        ('parent_id', [1, 'uint32']),
        ('title', [1, 'string']),
        ('command', [1, 'string']),
        ('command_type', [1, 'uint8']),
    ],
    'visualization_msgs/msg/MarkerArray': [
        ('markers', [4, [2, 'visualization_msgs/msg/Marker']]),
    ],
    'visualization_msgs/msg/InteractiveMarkerUpdate': [
        ('server_id', [1, 'string']),
        ('seq_num', [1, 'uint64']),
        ('type', [1, 'uint8']),
        ('markers', [4, [2, 'visualization_msgs/msg/InteractiveMarker']]),
        ('poses', [4, [2, 'visualization_msgs/msg/InteractiveMarkerPose']]),
        ('erases', [4, [1, 'string']]),
    ],
    'visualization_msgs/msg/InteractiveMarker': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('pose', [2, 'geometry_msgs/msg/Pose']),
        ('name', [1, 'string']),
        ('description', [1, 'string']),
        ('scale', [1, 'float32']),
        ('menu_entries', [4, [2, 'visualization_msgs/msg/MenuEntry']]),
        ('controls', [4, [2, 'visualization_msgs/msg/InteractiveMarkerControl']]),
    ],
    'visualization_msgs/msg/InteractiveMarkerFeedback': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('client_id', [1, 'string']),
        ('marker_name', [1, 'string']),
        ('control_name', [1, 'string']),
        ('event_type', [1, 'uint8']),
        ('pose', [2, 'geometry_msgs/msg/Pose']),
        ('menu_entry_id', [1, 'uint32']),
        ('mouse_point', [2, 'geometry_msgs/msg/Point']),
        ('mouse_point_valid', [1, 'bool']),
    ],
    'visualization_msgs/msg/ImageMarker': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('ns', [1, 'string']),
        ('id', [1, 'int32']),
        ('type', [1, 'int32']),
        ('action', [1, 'int32']),
        ('position', [2, 'geometry_msgs/msg/Point']),
        ('scale', [1, 'float32']),
        ('outline_color', [2, 'std_msgs/msg/ColorRGBA']),
        ('filled', [1, 'uint8']),
        ('fill_color', [2, 'std_msgs/msg/ColorRGBA']),
        ('lifetime', [2, 'builtin_interfaces/msg/Duration']),
        ('points', [4, [2, 'geometry_msgs/msg/Point']]),
        ('outline_colors', [4, [2, 'std_msgs/msg/ColorRGBA']]),
    ],
    'visualization_msgs/msg/InteractiveMarkerControl': [
        ('name', [1, 'string']),
        ('orientation', [2, 'geometry_msgs/msg/Quaternion']),
        ('orientation_mode', [1, 'uint8']),
        ('interaction_mode', [1, 'uint8']),
        ('always_visible', [1, 'bool']),
        ('markers', [4, [2, 'visualization_msgs/msg/Marker']]),
        ('independent_marker_orientation', [1, 'bool']),
        ('description', [1, 'string']),
    ],
    'visualization_msgs/msg/InteractiveMarkerPose': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('pose', [2, 'geometry_msgs/msg/Pose']),
        ('name', [1, 'string']),
    ],
    'autoware_auto_msgs/msg/BoundingBox': [
        ('centroid', [2, 'geometry_msgs/msg/Point32']),
        ('size', [2, 'geometry_msgs/msg/Point32']),
        ('orientation', [2, 'autoware_auto_msgs/msg/Quaternion32']),
        ('velocity', [1, 'float32']),
        ('heading', [1, 'float32']),
        ('heading_rate', [1, 'float32']),
        ('corners', [3, 4, [2, 'geometry_msgs/msg/Point32']]),
        ('variance', [3, 8, [1, 'float32']]),
        ('value', [1, 'float32']),
        ('vehicle_label', [1, 'uint8']),
        ('signal_label', [1, 'uint8']),
        ('class_likelihood', [1, 'float32']),
    ],
    'autoware_auto_msgs/msg/HADMapBin': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('map_format', [1, 'uint8']),
        ('format_version', [1, 'string']),
        ('map_version', [1, 'string']),
        ('data', [4, [1, 'uint8']]),
    ],
    'autoware_auto_msgs/msg/Quaternion32': [
        ('x', [1, 'float32']),
        ('y', [1, 'float32']),
        ('z', [1, 'float32']),
        ('w', [1, 'float32']),
    ],
    'autoware_auto_msgs/msg/Trajectory': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('points', [4, [2, 'autoware_auto_msgs/msg/TrajectoryPoint']]),
    ],
    'autoware_auto_msgs/msg/Route': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('start_point', [2, 'autoware_auto_msgs/msg/TrajectoryPoint']),
        ('goal_point', [2, 'autoware_auto_msgs/msg/TrajectoryPoint']),
        ('primitives', [4, [2, 'autoware_auto_msgs/msg/MapPrimitive']]),
    ],
    'autoware_auto_msgs/msg/MapPrimitive': [
        ('id', [1, 'int64']),
        ('primitive_type', [1, 'string']),
    ],
    'autoware_auto_msgs/msg/TrajectoryPoint': [
        ('time_from_start', [2, 'builtin_interfaces/msg/Duration']),
        ('x', [1, 'float32']),
        ('y', [1, 'float32']),
        ('heading', [2, 'autoware_auto_msgs/msg/Complex32']),
        ('longitudinal_velocity_mps', [1, 'float32']),
        ('lateral_velocity_mps', [1, 'float32']),
        ('acceleration_mps2', [1, 'float32']),
        ('heading_rate_rps', [1, 'float32']),
        ('front_wheel_angle_rad', [1, 'float32']),
        ('rear_wheel_angle_rad', [1, 'float32']),
    ],
    'autoware_auto_msgs/msg/Complex32': [
        ('real', [1, 'float32']),
        ('imag', [1, 'float32']),
    ],
    'autoware_auto_msgs/msg/VehicleOdometry': [
        ('stamp', [2, 'builtin_interfaces/msg/Time']),
        ('velocity_mps', [1, 'float32']),
        ('front_wheel_angle_rad', [1, 'float32']),
        ('rear_wheel_angle_rad', [1, 'float32']),
    ],
    'autoware_auto_msgs/msg/DiagnosticHeader': [
        ('name', [1, 'string', [6, 256]]),
        ('data_stamp', [2, 'builtin_interfaces/msg/Time']),
        ('computation_start', [2, 'builtin_interfaces/msg/Time']),
        ('runtime', [2, 'builtin_interfaces/msg/Duration']),
        ('iterations', [1, 'uint32']),
    ],
    'autoware_auto_msgs/msg/HighLevelControlCommand': [
        ('stamp', [2, 'builtin_interfaces/msg/Time']),
        ('velocity_mps', [1, 'float32']),
        ('curvature', [1, 'float32']),
    ],
    'autoware_auto_msgs/msg/VehicleStateCommand': [
        ('stamp', [2, 'builtin_interfaces/msg/Time']),
        ('blinker', [1, 'uint8']),
        ('headlight', [1, 'uint8']),
        ('wiper', [1, 'uint8']),
        ('gear', [1, 'uint8']),
        ('mode', [1, 'uint8']),
        ('hand_brake', [1, 'bool']),
        ('horn', [1, 'bool']),
    ],
    'autoware_auto_msgs/msg/PointClusters': [
        ('clusters', [4, [2, 'sensor_msgs/msg/PointCloud2']]),
    ],
    'autoware_auto_msgs/msg/RawControlCommand': [
        ('stamp', [2, 'builtin_interfaces/msg/Time']),
        ('throttle', [1, 'uint32']),
        ('brake', [1, 'uint32']),
        ('front_steer', [1, 'int32']),
        ('rear_steer', [1, 'int32']),
    ],
    'autoware_auto_msgs/msg/VehicleStateReport': [
        ('stamp', [2, 'builtin_interfaces/msg/Time']),
        ('fuel', [1, 'uint8']),
        ('blinker', [1, 'uint8']),
        ('headlight', [1, 'uint8']),
        ('wiper', [1, 'uint8']),
        ('gear', [1, 'uint8']),
        ('mode', [1, 'uint8']),
        ('hand_brake', [1, 'bool']),
        ('horn', [1, 'bool']),
    ],
    'autoware_auto_msgs/msg/ControlDiagnostic': [
        ('diag_header', [2, 'autoware_auto_msgs/msg/DiagnosticHeader']),
        ('new_trajectory', [1, 'bool']),
        ('trajectory_source', [1, 'string', [6, 256]]),
        ('pose_source', [1, 'string', [6, 256]]),
        ('lateral_error_m', [1, 'float32']),
        ('longitudinal_error_m', [1, 'float32']),
        ('velocity_error_mps', [1, 'float32']),
        ('acceleration_error_mps2', [1, 'float32']),
        ('yaw_error_rad', [1, 'float32']),
        ('yaw_rate_error_rps', [1, 'float32']),
    ],
    'autoware_auto_msgs/msg/VehicleKinematicState': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('state', [2, 'autoware_auto_msgs/msg/TrajectoryPoint']),
        ('delta', [2, 'geometry_msgs/msg/Transform']),
    ],
    'autoware_auto_msgs/msg/BoundingBoxArray': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('boxes', [4, [2, 'autoware_auto_msgs/msg/BoundingBox']]),
    ],
    'autoware_auto_msgs/msg/VehicleControlCommand': [
        ('stamp', [2, 'builtin_interfaces/msg/Time']),
        ('long_accel_mps2', [1, 'float32']),
        ('velocity_mps', [1, 'float32']),
        ('front_wheel_angle_rad', [1, 'float32']),
        ('rear_wheel_angle_rad', [1, 'float32']),
    ],
    'automotive_navigation_msgs/msg/CommandWithHandshake': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('msg_counter', [1, 'uint8']),
        ('command', [1, 'int16']),
    ],
    'automotive_navigation_msgs/msg/DesiredDestination': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('msg_counter', [1, 'uint8']),
        ('valid', [1, 'uint16']),
        ('latitude', [1, 'float64']),
        ('longitude', [1, 'float64']),
    ],
    'automotive_navigation_msgs/msg/Direction': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('direction', [1, 'int8']),
    ],
    'automotive_navigation_msgs/msg/DistanceToDestination': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('msg_counter', [1, 'uint8']),
        ('distance', [1, 'float32']),
    ],
    'automotive_navigation_msgs/msg/LaneBoundary': [
        ('style', [1, 'uint8']),
        ('color', [1, 'uint8']),
        ('line', [4, [2, 'geometry_msgs/msg/Point']]),
    ],
    'automotive_navigation_msgs/msg/LaneBoundaryArray': [
        ('boundaries', [4, [2, 'automotive_navigation_msgs/msg/LaneBoundary']]),
    ],
    'automotive_navigation_msgs/msg/ModuleState': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('name', [1, 'string']),
        ('state', [1, 'string']),
        ('info', [1, 'string']),
    ],
    'automotive_navigation_msgs/msg/PointOfInterest': [
        ('guid', [1, 'uint64']),
        ('latitude', [1, 'float64']),
        ('longitude', [1, 'float64']),
        ('params', [1, 'string']),
    ],
    'automotive_navigation_msgs/msg/PointOfInterestArray': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('update_num', [1, 'uint16']),
        ('point_list', [4, [2, 'automotive_navigation_msgs/msg/PointOfInterest']]),
    ],
    'automotive_navigation_msgs/msg/PointOfInterestRequest': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('name', [1, 'string']),
        ('module_name', [1, 'string']),
        ('request_id', [1, 'uint16']),
        ('cancel', [1, 'uint16']),
        ('update_num', [1, 'uint16']),
        ('guid_valid', [1, 'uint16']),
        ('guid', [1, 'uint64']),
        ('tolerance', [1, 'float32']),
    ],
    'automotive_navigation_msgs/msg/PointOfInterestResponse': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('name', [1, 'string']),
        ('module_name', [1, 'string']),
        ('request_id', [1, 'uint16']),
        ('update_num', [1, 'uint16']),
        ('point_statuses', [4, [2, 'automotive_navigation_msgs/msg/PointOfInterestStatus']]),
    ],
    'automotive_navigation_msgs/msg/PointOfInterestStatus': [
        ('guid', [1, 'uint64']),
        ('distance', [1, 'float32']),
        ('heading', [1, 'float32']),
        ('x_position', [1, 'float32']),
        ('y_position', [1, 'float32']),
        ('params', [1, 'string']),
    ],
    'automotive_navigation_msgs/msg/RoadNetworkBoundaries': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('road_network_boundaries', [4, [2, 'automotive_navigation_msgs/msg/LaneBoundaryArray']]),
    ],
    'automotive_platform_msgs/msg/AdaptiveCruiseControlCommand': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('msg_counter', [1, 'uint8']),
        ('set_speed', [1, 'float32']),
        ('set', [1, 'uint16']),
        ('resume', [1, 'uint16']),
        ('cancel', [1, 'uint16']),
        ('speed_up', [1, 'uint16']),
        ('slow_down', [1, 'uint16']),
        ('further', [1, 'uint16']),
        ('closer', [1, 'uint16']),
    ],
    'automotive_platform_msgs/msg/AdaptiveCruiseControlSettings': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('set_speed', [1, 'float32']),
        ('following_spot', [1, 'uint16']),
        ('min_percent', [1, 'float32']),
        ('step_percent', [1, 'float32']),
        ('cipv_percent', [1, 'float32']),
        ('max_distance', [1, 'float32']),
    ],
    'automotive_platform_msgs/msg/BlindSpotIndicators': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('left', [1, 'bool']),
        ('right', [1, 'bool']),
    ],
    'automotive_platform_msgs/msg/BrakeCommand': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('brake_pedal', [1, 'float32']),
    ],
    'automotive_platform_msgs/msg/BrakeFeedback': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('brake_pedal', [1, 'float32']),
    ],
    'automotive_platform_msgs/msg/CabinReport': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('door_open_front_right', [1, 'bool']),
        ('door_open_front_left', [1, 'bool']),
        ('door_open_rear_right', [1, 'bool']),
        ('door_open_rear_left', [1, 'bool']),
        ('hood_open', [1, 'bool']),
        ('trunk_open', [1, 'bool']),
        ('passenger_present', [1, 'bool']),
        ('passenger_airbag_enabled', [1, 'bool']),
        ('seatbelt_engaged_driver', [1, 'bool']),
        ('seatbelt_engaged_passenger', [1, 'bool']),
    ],
    'automotive_platform_msgs/msg/CurvatureFeedback': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('curvature', [1, 'float32']),
    ],
    'automotive_platform_msgs/msg/DriverCommands': [
        ('msg_counter', [1, 'uint8']),
        ('engage', [1, 'uint16']),
        ('disengage', [1, 'uint16']),
        ('speed_up', [1, 'uint16']),
        ('slow_down', [1, 'uint16']),
        ('further', [1, 'uint16']),
        ('closer', [1, 'uint16']),
        ('right_turn', [1, 'uint16']),
        ('left_turn', [1, 'uint16']),
    ],
    'automotive_platform_msgs/msg/Gear': [
        ('gear', [1, 'uint8']),
    ],
    'automotive_platform_msgs/msg/GearCommand': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('command', [2, 'automotive_platform_msgs/msg/Gear']),
    ],
    'automotive_platform_msgs/msg/GearFeedback': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('current_gear', [2, 'automotive_platform_msgs/msg/Gear']),
    ],
    'automotive_platform_msgs/msg/HillStartAssist': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('active', [1, 'bool']),
    ],
    'automotive_platform_msgs/msg/Speed': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('module_name', [1, 'string']),
        ('speed', [1, 'float32']),
        ('acceleration_limit', [1, 'float32']),
        ('deceleration_limit', [1, 'float32']),
    ],
    'automotive_platform_msgs/msg/SpeedMode': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('mode', [1, 'uint16']),
        ('speed', [1, 'float32']),
        ('acceleration_limit', [1, 'float32']),
        ('deceleration_limit', [1, 'float32']),
    ],
    'automotive_platform_msgs/msg/SpeedPedals': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('mode', [1, 'uint16']),
        ('throttle', [1, 'float32']),
        ('brake', [1, 'float32']),
    ],
    'automotive_platform_msgs/msg/Steer': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('module_name', [1, 'string']),
        ('curvature', [1, 'float32']),
        ('max_curvature_rate', [1, 'float32']),
    ],
    'automotive_platform_msgs/msg/SteerMode': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('mode', [1, 'uint16']),
        ('curvature', [1, 'float32']),
        ('max_curvature_rate', [1, 'float32']),
    ],
    'automotive_platform_msgs/msg/SteerWheel': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('mode', [1, 'uint16']),
        ('angle', [1, 'float32']),
        ('angle_velocity', [1, 'float32']),
    ],
    'automotive_platform_msgs/msg/SteeringCommand': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('steering_wheel_angle', [1, 'float32']),
    ],
    'automotive_platform_msgs/msg/SteeringFeedback': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('steering_wheel_angle', [1, 'float32']),
    ],
    'automotive_platform_msgs/msg/ThrottleCommand': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('throttle_pedal', [1, 'float32']),
    ],
    'automotive_platform_msgs/msg/ThrottleFeedback': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('throttle_pedal', [1, 'float32']),
    ],
    'automotive_platform_msgs/msg/TurnSignalCommand': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('mode', [1, 'uint16']),
        ('turn_signal', [1, 'uint8']),
    ],
    'automotive_platform_msgs/msg/UserInputADAS': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('btn_cc_on', [1, 'bool']),
        ('btn_cc_off', [1, 'bool']),
        ('btn_cc_on_off', [1, 'bool']),
        ('btn_cc_set_inc', [1, 'bool']),
        ('btn_cc_set_dec', [1, 'bool']),
        ('btn_cc_res', [1, 'bool']),
        ('btn_cc_cncl', [1, 'bool']),
        ('btn_cc_res_cncl', [1, 'bool']),
        ('btn_acc_gap_inc', [1, 'bool']),
        ('btn_acc_gap_dec', [1, 'bool']),
        ('btn_lka_on', [1, 'bool']),
        ('btn_lka_off', [1, 'bool']),
        ('btn_lka_on_off', [1, 'bool']),
    ],
    'automotive_platform_msgs/msg/UserInputMedia': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('btn_vol_up', [1, 'bool']),
        ('btn_vol_down', [1, 'bool']),
        ('btn_mute', [1, 'bool']),
        ('btn_next', [1, 'bool']),
        ('btn_prev', [1, 'bool']),
        ('btn_next_hang_up', [1, 'bool']),
        ('btn_prev_answer', [1, 'bool']),
        ('btn_hang_up', [1, 'bool']),
        ('btn_answer', [1, 'bool']),
        ('btn_play', [1, 'bool']),
        ('btn_pause', [1, 'bool']),
        ('btn_play_pause', [1, 'bool']),
        ('btn_mode', [1, 'bool']),
    ],
    'automotive_platform_msgs/msg/UserInputMenus': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('str_whl_left_btn_left', [1, 'bool']),
        ('str_whl_left_btn_down', [1, 'bool']),
        ('str_whl_left_btn_right', [1, 'bool']),
        ('str_whl_left_btn_up', [1, 'bool']),
        ('str_whl_left_btn_ok', [1, 'bool']),
        ('str_whl_right_btn_left', [1, 'bool']),
        ('str_whl_right_btn_down', [1, 'bool']),
        ('str_whl_right_btn_right', [1, 'bool']),
        ('str_whl_right_btn_up', [1, 'bool']),
        ('str_whl_right_btn_ok', [1, 'bool']),
        ('cntr_cons_btn_left', [1, 'bool']),
        ('cntr_cons_btn_down', [1, 'bool']),
        ('cntr_cons_btn_right', [1, 'bool']),
        ('cntr_cons_btn_up', [1, 'bool']),
        ('cntr_cons_btn_ok', [1, 'bool']),
    ],
    'automotive_platform_msgs/msg/VelocityAccel': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('velocity', [1, 'float32']),
        ('accleration', [1, 'float32']),
    ],
    'automotive_platform_msgs/msg/VelocityAccelCov': [
        ('header', [2, 'std_msgs/msg/Header']),
        ('velocity', [1, 'float32']),
        ('accleration', [1, 'float32']),
        ('covariance', [1, 'float32']),
    ],
}
