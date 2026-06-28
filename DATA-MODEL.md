# iRacing Telemetry Analyzer — Data Model

Status: Draft v1  
Purpose: Define the canonical data contracts before writing more analysis logic.

This document describes the clean application data model for the iRacing telemetry analyzer. It is intentionally written from the TypeScript runtime consumer's point of view.

Python may generate some static files, especially track geometry JSON, but the long-term runtime analysis layer consumes the models defined here.

---

## 1. Core principles

### 1.1 Raw iRacing data is parsed at the boundary

Raw iRacing field names such as `Speed`, `LapDistPct`, `SessionTime`, and `SteeringWheelAngle` should only be used in the parser/config layer.

Application logic should use normalized names such as `speedMetersPerSecond`, `lapDistPct`, `sessionTimeSeconds`, and `steeringWheelAngleRadians`.

This prevents raw SDK naming from leaking into analysis code and avoids key-name drift.

### 1.2 Static track data and driven lap data are separate

A `Corner` describes where a corner is on the circuit.

A `CornerPerformance` describes how one lap was driven through that corner.

These must never be merged.

### 1.3 Track geometry is part of the TrackModel

The `TrackModel` is the canonical static model for one circuit/configuration. It contains both analysis data and frontend display geometry.

This means the same file can answer:

- What track is this?
- How should it be drawn?
- Where are the sectors?
- Where are the static corners?

### 1.4 Session data links to TrackModel by trackId

A `Session` does not duplicate track geometry.

Instead, the parsed session metadata contains the iRacing `trackId`, and the app uses that to load the matching `TrackModel`.

### 1.5 Use lap-distance percentages for analysis boundaries

Fields ending in `DistPct` are normalized lap-distance fractions.

They must be in the range:

```text
0.0 <= value <= 1.0
```

Meaning:

- `0.0` = start/finish line
- `1.0` = end of lap

Analysis logic should prefer `lapDistPct` over absolute metres when bucketing samples into sectors/corners or comparing laps.

### 1.6 Explicit units in field names

If a field stores a measured unit, the unit should usually appear in the field name.

Preferred examples:

- `trackLengthMeters`
- `distanceMeters`
- `widthMeters`
- `speedMetersPerSecond`
- `sessionTimeSeconds`
- `lapTimeSeconds`
- `maxCurvatureDegPerMeter`

Avoid vague names such as `distance`, `speed`, `time`, or `maxCurvature` in clean app models.

---

## 2. Model overview

```text
Raw iRacing telemetry channels
        ↓
TelemetrySample
        ↓
Lap
        ↓
Session

TrackModel
 ├── Sector
 └── Corner

Lap
 └── LapAnalysis
      ├── SectorPerformance
      └── CornerPerformance

LapAnalysis + LapAnalysis
        ↓
LapComparison
 ├── LapDeltaPoint[]
 ├── SectorComparison[]
 └── CornerComparison[]
```

---

## 3. Parser/config boundary

The parser boundary is responsible for converting raw iRacing data into clean app models.

### 3.1 AvailableTelemetryChannels

`AvailableTelemetryChannels` is the complete list of telemetry channels present in the `.ibt` file.

It contains raw iRacing names and is used for validation/debugging only.

Example raw channel names:

```text
SessionTime
SessionTick
Lap
LapDistPct
Speed
Throttle
Brake
SteeringWheelAngle
YawRate
LatAccel
LongAccel
```

### 3.2 wantedTelemetryChannels

`wantedTelemetryChannels` is the central parser config list of raw iRacing channels that should be extracted for `TelemetrySample` v1.

Recommended v1 raw channel list:

| Raw iRacing channel | Used for normalized field |
|---|---|
| `SessionTime` | `sessionTimeSeconds` |
| `SessionTick` | `sessionTick` |
| `Lap` | `lapNumber` |
| `LapCompleted` | `lapCompleted` |
| `LapDist` | `lapDistMeters` |
| `LapDistPct` | `lapDistPct` |
| `Speed` | `speedMetersPerSecond` |
| `Throttle` | `throttle` |
| `Brake` | `brake` |
| `Clutch` | `clutch` |
| `Gear` | `gear` |
| `RPM` | `rpm` |
| `SteeringWheelAngle` | `steeringWheelAngleRadians` |
| `YawRate` | `yawRate` |
| `LatAccel` | `latAccel` |
| `LongAccel` | `longAccel` |
| `IsOnTrack` | `isOnTrack` |
| `OnPitRoad` | `onPitRoad` |
| `PlayerTrackSurface` | `playerTrackSurface` |

### 3.3 rawToNormalizedChannelMap

The raw-to-normalized mapping should define, in one place:

- raw iRacing channel name
- normalized app field name
- unit or scale
- whether the channel is required
- what the field is used for

Required v1 channels should cause parsing to fail clearly if missing.

Optional v1 channels should allow parsing to continue, with the normalized field set to `null` or omitted according to the TypeScript type.

### 3.4 Future telemetry channel groups

Do not add these to `TelemetrySample` v1 until a real feature needs them:

| Future group | Example raw fields | Intended use |
|---|---|---|
| `TyreChannels` | tyre temperature, pressure, wear | Tyre analysis |
| `FuelChannels` | fuel level, fuel use per hour | Fuel stint analysis |
| `EngineChannels` | oil temp, water temp, voltage | Engine health/context |
| `SuspensionChannels` | shock deflection, shock velocity, ride height | Vehicle dynamics analysis |
| `WeatherChannels` | air temp, track temp, wind, humidity | Session comparison context |
| `RawInputChannels` | `ThrottleRaw`, `BrakeRaw`, `ClutchRaw` | Input hardware/debug analysis |
| `GpsChannels` | `Lat`, `Lon`, `Alt` | Future map/debug features |

---

## 4. TrackModel

`TrackModel` is one canonical static circuit model.

It owns:

- track identity
- generation metadata
- coordinate system
- frontend geometry
- sectors
- static corners

It must not contain driven lap data.

### 4.1 Shape

```text
TrackModel
├── schemaVersion
├── track
├── generation
├── coordinateSystem
├── geometry
│   ├── centerline
│   ├── leftBoundary
│   └── rightBoundary
├── sectors
└── corners
```

### 4.2 Top-level fields

| Field | Type | Required | Contains / represents |
|---|---:|---:|---|
| `schemaVersion` | number | yes | Version of this JSON schema. Start at `1`. |
| `track` | object | yes | Identity and basic facts for the circuit/configuration. |
| `generation` | object | yes | Metadata about how this file was generated. |
| `coordinateSystem` | object | yes | How to interpret geometry coordinates. |
| `geometry` | object | yes | Centerline and boundary geometry for display/mapping. |
| `sectors` | `Sector[]` | yes | Static sector start positions. |
| `corners` | `Corner[]` | yes | Static geometric corner regions. |

---

## 5. TrackModel.track

`track` describes the real circuit/configuration represented by the model.

| Field | Type | Required | Unit | Contains / represents |
|---|---:|---:|---:|---|
| `trackId` | number | yes | none | iRacing TrackID. Primary key for matching a `Session` to this model. |
| `name` | string | yes | none | Human-readable circuit name, e.g. `Okayama International Circuit`. |
| `configName` | string | yes | none | Layout/config name, e.g. `Full Course`. |
| `slug` | string | yes | none | Stable app/file-friendly identifier, e.g. `okayama-full-course`. |
| `country` | string | optional | none | Country for display/debugging, e.g. `Japan`. |
| `trackLengthMeters` | number | yes | metres | Full closed-loop centreline lap length used by this model. |
| `closed` | boolean | yes | none | Whether this model represents a closed circuit loop. Normal road circuits should be `true`. |

### 5.1 Track length rule

`trackLengthMeters` should represent the full closed-loop centreline length.

If `closed` is `true`, it should include the final segment from the last centreline point back to the first point.

---

## 6. TrackModel.generation

`generation` describes how this model file was produced.

It does not describe the real circuit itself.

| Field | Type | Required | Contains / represents |
|---|---:|---:|---|
| `generatedAt` | string | yes | ISO timestamp when the model was generated. |
| `source` | string | yes | Tool/script used to generate the file, e.g. `exportTrackGeometry.py`. |
| `pointCount` | number | yes | Number of resampled geometry points per line. |
| `notes` | string | optional | Human-readable notes about validation, source KML, or known limitations. |

---

## 7. TrackModel.coordinateSystem

`coordinateSystem` explains how geometry coordinates should be interpreted.

| Field | Type | Required | Contains / represents |
|---|---:|---:|---|
| `type` | string | yes | Coordinate system type. Use `local_xy_meters`. |
| `originLat` | number | yes | Latitude used as the local coordinate origin. |
| `originLon` | number | yes | Longitude used as the local coordinate origin. |
| `xUnit` | string | yes | Unit of `x`. Use `meters`. |
| `yUnit` | string | yes | Unit of `y`. Use `meters`. |

### 7.1 Coordinate rule

`x` and `y` are the authoritative geometry/display coordinates.

Point-level `lat` and `lon` values are reference values only and should not be used as the source of truth for analysis.

---

## 8. TrackModel.geometry

`geometry` contains the points needed to draw the circuit and map lap positions onto the track shape.

| Field | Type | Required | Contains / represents |
|---|---:|---:|---|
| `centerline` | object | yes | Resampled centreline geometry. |
| `leftBoundary` | object | yes | Resampled left boundary geometry. |
| `rightBoundary` | object | yes | Resampled right boundary geometry. |

### 8.1 BoundaryPoint

Used by:

- `geometry.leftBoundary.points[]`
- `geometry.rightBoundary.points[]`

| Field | Type | Required | Unit | Contains / represents |
|---|---:|---:|---:|---|
| `x` | number | yes | metres | Local x-coordinate. |
| `y` | number | yes | metres | Local y-coordinate. |
| `lat` | number | optional | degrees | Reference GPS latitude. Not authoritative for analysis. |
| `lon` | number | optional | degrees | Reference GPS longitude. Not authoritative for analysis. |
| `distanceMeters` | number | yes | metres | Distance along this boundary from its first point. |

### 8.2 CenterlinePoint

Used by:

- `geometry.centerline.points[]`

| Field | Type | Required | Unit | Contains / represents |
|---|---:|---:|---:|---|
| `x` | number | yes | metres | Local centreline x-coordinate. |
| `y` | number | yes | metres | Local centreline y-coordinate. |
| `lat` | number | optional | degrees | Reference GPS latitude. Not authoritative for analysis. |
| `lon` | number | optional | degrees | Reference GPS longitude. Not authoritative for analysis. |
| `distanceMeters` | number | yes | metres | Distance around the centreline from start/finish. |
| `widthMeters` | number | optional | metres | Estimated track width at this centreline point. |
| `normalX` | number | optional | none | Unit normal x-direction used during generation/debug/display. |
| `normalY` | number | optional | none | Unit normal y-direction used during generation/debug/display. |

---

## 9. Sector

A `Sector` is a static split region on the track.

Sectors are manually authored in the `TrackModel` as start percentages only.

Track model creation must not depend on session telemetry or `.ibt` session info.

### 9.1 Shape

| Field | Type | Required | Unit | Contains / represents |
|---|---:|---:|---:|---|
| `sectorId` | number | yes | none | 1-based sector number. |
| `startDistPct` | number | yes | 0–1 fraction | Where this sector starts around the lap. |

### 9.2 Derived sector end rule

`endDistPct` is not stored in the `TrackModel`.

It is derived in code:

- sector 1 starts at `0.0`
- a sector ends at the next sector's `startDistPct`
- the final sector ends at `1.0`

---

## 10. Corner

A `Corner` is a static geometric corner region from the `TrackModel`.

It describes where the corner is, not how a driver drove it.

### 10.1 Shape

| Field | Type | Required | Unit | Contains / represents |
|---|---:|---:|---:|---|
| `cornerId` | number | yes | none | 1-based corner ID. |
| `name` | string | optional | none | Optional display label, e.g. `Turn 1` or `Hairpin`. |
| `startDistPct` | number | yes | 0–1 fraction | Start of the static corner region. |
| `apexDistPct` | number | yes | 0–1 fraction | Geometric apex: max-curvature point of the corner. |
| `endDistPct` | number | yes | 0–1 fraction | End of the static corner region. |
| `maxCurvatureDegPerMeter` | number | yes | degrees/metre | Peak geometric curvature inside this corner. |

### 10.2 Corner wraparound rule

If:

```text
endDistPct < startDistPct
```

then the corner crosses the start/finish line.

A sample is inside that corner if:

```text
lapDistPct >= startDistPct OR lapDistPct <= endDistPct
```

---

## 11. RawSessionInfo parser boundary

`sessionInfo.txt` is raw session metadata from iRacing.

It should be parsed once at the boundary and normalized into clean session-level objects.

Raw session info field names should not leak into analysis code.

SessionInfo must not create or modify `TrackModel` geometry, corners, or sectors.

### 11.1 Normalized outputs

Raw session info should feed:

```text
Session.metadata
Session.trackModelRef
Session.participants
Session.player
Session.car
Session.environment
Session.results
```

### 11.2 SessionMetadata

`SessionMetadata` describes the identity and context of the iRacing session/recording.

| Field | Type | Required | Contains / represents |
|---|---:|---:|---|
| `sessionId` | number/string | optional | iRacing SessionID, when available. |
| `subSessionId` | number/string | optional | iRacing SubSessionID/split identifier, when available. |
| `sessionNum` | number | optional | Session number within the weekend. |
| `sessionType` | string | optional | Practice, qualifying, race, etc. |
| `sessionName` | string | optional | Display name for the session, e.g. `PRACTICE`. |
| `eventType` | string | optional | iRacing event type, e.g. `Practice`. |
| `category` | string | optional | Racing category, e.g. `SportsCar` or `Formula`. |
| `official` | boolean | optional | Whether the session was official. |
| `seriesId` | number | optional | iRacing series ID. |
| `seasonId` | number | optional | iRacing season ID. |
| `raceWeek` | number | optional | Race week number. |
| `simMode` | string | optional | iRacing sim mode, e.g. `full`. |
| `teamRacing` | boolean | optional | Whether the session used team racing. |
| `trackId` | number | yes | iRacing TrackID used to load the matching `TrackModel`. |
| `trackName` | string | optional | Raw/session track name. |
| `trackDisplayName` | string | optional | Human-readable track display name. |
| `trackDisplayShortName` | string | optional | Short display name. |
| `trackConfigName` | string | optional | Track layout/config name. |
| `trackCity` | string | optional | Track city. |
| `trackCountry` | string | optional | Track country. |
| `trackLengthText` | string | optional | Session-reported track length text, e.g. `3.65 km`. Reference only. |
| `trackLengthOfficialText` | string | optional | Official track length text, e.g. `3.72 km`. Reference only. |
| `trackPitSpeedLimitKph` | number | optional | Pit speed limit in kph. |
| `trackNumTurns` | number | optional | iRacing-reported turn count. Reference only. |
| `trackVersion` | string | optional | iRacing track version string. |

### 11.3 TrackModelRef

`TrackModelRef` links a parsed session to the static track model.

| Field | Type | Required | Contains / represents |
|---|---:|---:|---|
| `trackId` | number | yes | iRacing TrackID used for lookup. |
| `trackSlug` | string | optional | App slug for the matched track model, e.g. `okayama-full-course`. |
| `trackModelVersion` | number | optional | Matched `TrackModel.schemaVersion`. |

### 11.4 ParticipantInfo

`ParticipantInfo` describes one driver/car listed in the session.

| Field | Type | Required | Contains / represents |
|---|---:|---:|---|
| `carIdx` | number | yes | iRacing car index. Used to connect session info to telemetry car references. |
| `userName` | string | optional | Driver/user display name. |
| `userId` | number/string | optional | iRacing user ID. |
| `teamName` | string | optional | Team name. |
| `carNumber` | string | optional | Display car number. |
| `carPath` | string | optional | iRacing car path identifier. |
| `carId` | number | optional | iRacing car ID. |
| `carClassId` | number | optional | iRacing car class ID. |
| `carScreenName` | string | optional | Full car display name. |
| `carClassShortName` | string | optional | Short car class name. |
| `iRating` | number | optional | Driver iRating at session time. |
| `licenseString` | string | optional | Driver licence string. |
| `isSpectator` | boolean | optional | Whether this entry is a spectator. |

### 11.5 PlayerInfo

`PlayerInfo` describes the driver/car that the telemetry file primarily belongs to.

| Field | Type | Required | Contains / represents |
|---|---:|---:|---|
| `driverCarIdx` | number | optional | Car index for the player/recorded driver. |
| `driverUserId` | number/string | optional | iRacing user ID for the player. |
| `driverIncidentCount` | number | optional | Incident count reported for the player. |

### 11.6 CarInfo

`CarInfo` describes the player car.

| Field | Type | Required | Contains / represents |
|---|---:|---:|---|
| `carId` | number | optional | iRacing car ID. |
| `carPath` | string | optional | iRacing car path identifier. |
| `carScreenName` | string | optional | Full display name for the car. |
| `carScreenNameShort` | string | optional | Short display name for the car. |
| `carClassId` | number | optional | iRacing car class ID. |
| `carClassShortName` | string | optional | Short class name. |
| `carClassRelSpeed` | number | optional | Relative speed indicator from session info. |
| `carIsElectric` | boolean | optional | Whether the car is electric. |
| `carGearNumForward` | number | optional | Number of forward gears. |
| `carFuelMaxLiters` | number | optional | Maximum fuel capacity in litres. |
| `carFuelKgPerLiter` | number | optional | Fuel density value from iRacing. |
| `carRedLineRpm` | number | optional | Redline RPM. |
| `carShiftLightFirstRpm` | number | optional | First shift-light RPM. |
| `carShiftLightShiftRpm` | number | optional | Recommended shift-light RPM. |
| `carShiftLightLastRpm` | number | optional | Final shift-light RPM. |
| `carShiftLightBlinkRpm` | number | optional | Blink RPM. |
| `carVersion` | string | optional | iRacing car version string. |
| `estimatedLapTimeSeconds` | number | optional | Estimated lap time from iRacing, if available. Reference only. |

### 11.7 EnvironmentInfo

`EnvironmentInfo` describes session weather and track conditions.

| Field | Type | Required | Contains / represents |
|---|---:|---:|---|
| `trackSurfaceTempCelsius` | number | optional | Track surface temperature. |
| `trackAirTempCelsius` | number | optional | Air temperature. |
| `trackAirPressure` | string/number | optional | Air pressure as reported by iRacing. Normalize units later if needed. |
| `trackWindVelocityMetersPerSecond` | number | optional | Wind velocity in m/s. |
| `trackWindDirectionRadians` | number | optional | Wind direction in radians. |
| `trackRelativeHumidityPercent` | number | optional | Relative humidity percentage. |
| `trackFogLevelPercent` | number | optional | Fog level percentage. |
| `trackPrecipitationPercent` | number | optional | Precipitation percentage. |
| `trackWeatherType` | string | optional | Weather type, e.g. `Realistic`. |
| `trackSkies` | string | optional | Skies setting, e.g. `Dynamic`. |
| `trackDynamicTrack` | boolean | optional | Whether dynamic track was enabled. |
| `trackCleanup` | boolean/number | optional | Track cleanup setting from iRacing. |

### 11.8 ResultsInfo

`ResultsInfo` stores iRacing results for reference/cross-checking only.

It is not the source of truth for the app's own lap analysis.

| Field | Type | Required | Contains / represents |
|---|---:|---:|---|
| `resultsPositions` | array | optional | iRacing result rows for drivers/cars. |
| `resultsFastestLap` | array/object | optional | iRacing-reported fastest lap data. |
| `resultsAverageLapTime` | number | optional | iRacing-reported average lap time. |
| `resultsOfficial` | boolean | optional | Whether results are official. |

---

## 12. TelemetrySample

`TelemetrySample` is the normalized minimal per-frame model used by analysis code.

It should contain only values needed for:

- lap construction
- lap comparison
- corner analysis
- graphing
- basic validity filtering

### 12.1 Shape

| Field | Type | Required | Unit/scale | Contains / represents |
|---|---:|---:|---:|---|
| `sessionTimeSeconds` | number | yes | seconds | Timestamp within the session. Main ordering/time field. |
| `sessionTick` | number | yes | tick/count | iRacing session tick. Useful for ordering/debugging. |
| `lapNumber` | number | yes | none | Lap number reported by iRacing. |
| `lapCompleted` | number | yes | count | Number of completed laps reported by iRacing. |
| `lapDistMeters` | number | yes | metres | Distance around current lap in metres. Useful for sanity checks. |
| `lapDistPct` | number | yes | 0–1 fraction | Main position field for analysis/comparison. |
| `speedMetersPerSecond` | number | yes | m/s | Vehicle speed. UI can convert to kph/mph. |
| `throttle` | number | yes | 0–1 | Driver throttle input. |
| `brake` | number | yes | 0–1 | Driver brake input. |
| `clutch` | number | optional | 0–1 | Driver clutch input. Useful later, not essential for v1. |
| `gear` | number | yes | integer | Current selected gear. |
| `rpm` | number | yes | rev/min | Engine RPM. |
| `steeringWheelAngleRadians` | number | yes | radians | Steering wheel angle. |
| `yawRate` | number | yes | confirm from metadata | Vehicle yaw rate. Useful for rotation analysis. |
| `latAccel` | number | yes | confirm from metadata | Lateral acceleration. Useful for cornering load. |
| `longAccel` | number | yes | confirm from metadata | Longitudinal acceleration. Useful for braking/acceleration analysis. |
| `isOnTrack` | boolean | yes | boolean | Whether iRacing considers the player on track. |
| `onPitRoad` | boolean | yes | boolean | Whether the player is on pit road. |
| `playerTrackSurface` | number/string | optional | enum/code | Track surface state/material code for the player. Useful for validity/debugging. |

### 12.2 Rule

Do not add a raw telemetry channel to `TelemetrySample` just because it exists.

Only add a field when a real analysis or UI feature needs it.

---

## 13. Lap

A `Lap` is one detected lap-like group of telemetry samples.

It is a data container, not an analysis result.

The parser should not silently discard laps. Out-laps, in-laps, pit laps, incomplete laps, and invalid laps should still be represented and marked.

### 13.1 Shape

| Field | Type | Required | Unit | Contains / represents |
|---|---:|---:|---:|---|
| `lapNumber` | number | yes | none | Lap number for this group, based on `TelemetrySample.lapNumber`. |
| `samples` | `TelemetrySample[]` | yes | none | Ordered samples belonging to this lap. |
| `startSessionTimeSeconds` | number | yes | seconds | Session time of the first sample in the lap. |
| `endSessionTimeSeconds` | number | yes | seconds | Session time of the final sample in the lap. |
| `lapTimeSeconds` | number/null | yes | seconds | Computed lap duration when available. Usually `end - start` for complete laps. |
| `startLapDistPct` | number | yes | 0–1 fraction | `lapDistPct` of the first sample. Useful for debugging incomplete laps. |
| `endLapDistPct` | number | yes | 0–1 fraction | `lapDistPct` of the final sample. Useful for debugging lap grouping. |
| `isComplete` | boolean | yes | boolean | Whether the lap appears to contain a full circuit pass. |
| `isValid` | boolean | yes | boolean | Whether the lap should be used for normal analysis/comparison. |
| `invalidReasons` | string[] | yes | none | Machine-readable reasons this lap is not valid. Empty when valid. |
| `sampleCount` | number | yes | count | Number of samples in this lap. Usually equals `samples.length`. |

### 13.2 Common invalid reasons

Suggested values:

```text
incomplete_lap
pit_road
off_track
missing_required_channel
missing_samples
lap_distance_jump
too_few_samples
```

---

## 14. Session

A `Session` is one parsed iRacing telemetry recording/session.

It owns parsed telemetry data and session context.

It links to `TrackModel` by `trackId` and does not duplicate track geometry.

### 14.1 Shape

```text
Session
├── metadata
├── trackModelRef
├── participants
├── player
├── car
├── environment
├── results
├── samples
├── laps
└── summary
```

### 14.2 Fields

| Field | Type | Required | Contains / represents |
|---|---:|---:|---|
| `metadata` | `SessionMetadata` | yes | Session identity, track identity, event type, category, series/season context. |
| `trackModelRef` | `TrackModelRef` | yes | Link to the matching `TrackModel`. |
| `participants` | `ParticipantInfo[]` | optional | All drivers/cars listed in session info. |
| `player` | `PlayerInfo` | optional | Driver/car this telemetry primarily belongs to. |
| `car` | `CarInfo` | optional | Player car details. |
| `environment` | `EnvironmentInfo` | optional | Weather/track condition context. |
| `results` | `ResultsInfo` | optional | iRacing result data for reference/cross-checking only. |
| `samples` | `TelemetrySample[]` | yes | Full ordered list of normalized telemetry samples. |
| `laps` | `Lap[]` | yes | Every detected lap-like group of samples. |
| `summary` | `SessionSummary` | yes | Derived summary for UI/debugging. |

### 14.3 SessionSummary

| Field | Type | Required | Unit | Contains / represents |
|---|---:|---:|---:|---|
| `sampleCount` | number | yes | count | Total number of normalized samples. |
| `lapCount` | number | yes | count | Total number of detected laps. |
| `validLapCount` | number | yes | count | Number of laps where `isValid` is true. |
| `completeLapCount` | number | yes | count | Number of laps where `isComplete` is true. |
| `fastestLapNumber` | number/null | yes | none | Fastest valid lap number, if available. |
| `fastestLapTimeSeconds` | number/null | yes | seconds | Fastest valid lap time, if available. |
| `sessionStartTimeSeconds` | number | yes | seconds | Time of the first parsed sample. |
| `sessionEndTimeSeconds` | number | yes | seconds | Time of the final parsed sample. |
| `durationSeconds` | number | yes | seconds | Parsed duration. Usually `sessionEndTimeSeconds - sessionStartTimeSeconds`. |

---

## 15. CornerPerformance

`CornerPerformance` is derived analysis data for one lap through one static `Corner`.

It must never be stored in `TrackModel`.

### 15.1 Shape

| Field | Type | Required | Unit/scale | Contains / represents |
|---|---:|---:|---:|---|
| `cornerId` | number | yes | none | Links to `TrackModel.corners[].cornerId`. |
| `lapNumber` | number | yes | none | Lap this performance belongs to. |
| `entryDistPct` | number | yes | 0–1 fraction | Entry/start point for the driven corner region. Usually `Corner.startDistPct`. |
| `drivenApexDistPct` | number/null | yes | 0–1 fraction | Driven apex/min-speed point for this lap. Distinct from `Corner.apexDistPct`. |
| `exitDistPct` | number | yes | 0–1 fraction | Exit/end point for the driven corner region. Usually `Corner.endDistPct`. |
| `entrySpeedMetersPerSecond` | number/null | yes | m/s | Speed at corner entry. |
| `minSpeedMetersPerSecond` | number/null | yes | m/s | Minimum speed inside the corner region. |
| `exitSpeedMetersPerSecond` | number/null | yes | m/s | Speed at corner exit. |
| `brakeStartDistPct` | number/null | yes | 0–1 fraction | First braking point for the corner, if detected. |
| `brakeEndDistPct` | number/null | yes | 0–1 fraction | End of braking for the corner, if detected. |
| `maxBrake` | number/null | yes | 0–1 | Maximum brake value inside the corner region. |
| `throttlePickupDistPct` | number/null | yes | 0–1 fraction | Point where driver starts getting back on throttle, if detected. |
| `maxThrottle` | number/null | yes | 0–1 | Maximum throttle value inside the corner region. |
| `minGear` | number/null | yes | integer | Lowest gear used inside the corner region. |
| `maxLatAccel` | number/null | yes | confirm from metadata | Highest lateral acceleration inside the corner region. |
| `maxLongAccel` | number/null | yes | confirm from metadata | Highest longitudinal acceleration inside the corner region. |
| `sampleCount` | number | yes | count | Number of samples used for this corner analysis. |
| `isValid` | boolean | yes | boolean | Whether this corner performance should be trusted. |
| `invalidReasons` | string[] | yes | none | Reasons this corner performance is invalid. Empty when valid. |

### 15.2 Apex naming rule

`Corner.apexDistPct` means geometric apex from static track curvature.

`CornerPerformance.drivenApexDistPct` means driven apex/min-speed point for a specific lap.

These are different concepts and do not have to match.

---

## 16. SectorPerformance

`SectorPerformance` is derived analysis data for one lap through one static `Sector`.

### 16.1 Shape

| Field | Type | Required | Unit | Contains / represents |
|---|---:|---:|---:|---|
| `sectorId` | number | yes | none | Links to `TrackModel.sectors[].sectorId`. |
| `lapNumber` | number | yes | none | Lap this sector performance belongs to. |
| `startDistPct` | number | yes | 0–1 fraction | Sector start used for this calculation. |
| `endDistPct` | number | yes | 0–1 fraction | Derived sector end used for this calculation. |
| `sectorTimeSeconds` | number/null | yes | seconds | Time spent in this sector for the lap. |
| `sampleCount` | number | yes | count | Number of samples used for this sector. |
| `isValid` | boolean | yes | boolean | Whether the sector performance should be trusted. |
| `invalidReasons` | string[] | yes | none | Reasons this sector performance is invalid. Empty when valid. |

---

## 17. LapAnalysis

`LapAnalysis` is derived analysis for one lap by itself.

It contains lap-level summary metrics, sector performances, and corner performances.

It does not contain lap-vs-lap delta data.

### 17.1 Shape

```text
LapAnalysis
├── lapNumber
├── lapTimeSeconds
├── isComplete
├── isValid
├── invalidReasons
├── cornerPerformances
├── sectorPerformances
└── summary
```

### 17.2 Fields

| Field | Type | Required | Contains / represents |
|---|---:|---:|---|
| `lapNumber` | number | yes | Lap this analysis belongs to. |
| `lapTimeSeconds` | number/null | yes | Lap time copied/derived from the `Lap`. |
| `isComplete` | boolean | yes | Whether the source lap was complete. |
| `isValid` | boolean | yes | Whether this lap analysis should be used for normal comparison. |
| `invalidReasons` | string[] | yes | Lap-level and analysis-level invalid reasons. Empty when valid. |
| `cornerPerformances` | `CornerPerformance[]` | yes | Driven performance through each static corner. |
| `sectorPerformances` | `SectorPerformance[]` | yes | Driven performance through each static sector. |
| `summary` | `LapAnalysisSummary` | yes | Lap-level derived summary values. |

### 17.3 LapAnalysisSummary

| Field | Type | Required | Unit/scale | Contains / represents |
|---|---:|---:|---:|---|
| `maxSpeedMetersPerSecond` | number/null | yes | m/s | Maximum speed in the lap. |
| `minSpeedMetersPerSecond` | number/null | yes | m/s | Minimum speed in the lap. |
| `averageSpeedMetersPerSecond` | number/null | yes | m/s | Average speed across parsed lap samples. |
| `maxThrottle` | number/null | yes | 0–1 | Maximum throttle in the lap. |
| `averageThrottle` | number/null | yes | 0–1 | Average throttle across lap samples. |
| `maxBrake` | number/null | yes | 0–1 | Maximum brake in the lap. |
| `averageBrake` | number/null | yes | 0–1 | Average brake across lap samples. |
| `maxLatAccel` | number/null | yes | confirm from metadata | Maximum lateral acceleration in the lap. |
| `maxLongAccel` | number/null | yes | confirm from metadata | Maximum longitudinal acceleration in the lap. |
| `minGear` | number/null | yes | integer | Lowest gear used in the lap. |
| `maxGear` | number/null | yes | integer | Highest gear used in the lap. |
| `cornerCount` | number | yes | count | Number of corner performance objects. |
| `validCornerCount` | number | yes | count | Number of valid corner performance objects. |
| `sectorCount` | number | yes | count | Number of sector performance objects. |
| `validSectorCount` | number | yes | count | Number of valid sector performance objects. |

---

## 18. LapComparison

`LapComparison` is a derived comparison between two laps.

It compares two laps at matching `lapDistPct` positions using interpolation.

It owns delta trace data, corner deltas, and sector deltas.

It does not modify `Lap`, `LapAnalysis`, `CornerPerformance`, or `TrackModel`.

### 18.1 Sign convention

```text
deltaSeconds = comparisonLap - referenceLap
```

Meaning:

- positive delta = comparison lap is slower / lost time
- negative delta = comparison lap is faster / gained time

This convention must be used for total lap delta, sector delta, and corner delta.

### 18.2 Shape

```text
LapComparison
├── referenceLapNumber
├── comparisonLapNumber
├── referenceLapTimeSeconds
├── comparisonLapTimeSeconds
├── totalDeltaSeconds
├── deltaTrace
├── cornerComparisons
├── sectorComparisons
├── isValid
├── invalidReasons
└── summary
```

### 18.3 Fields

| Field | Type | Required | Unit | Contains / represents |
|---|---:|---:|---:|---|
| `referenceLapNumber` | number | yes | none | Lap used as the baseline. |
| `comparisonLapNumber` | number | yes | none | Lap compared against the reference. |
| `referenceLapTimeSeconds` | number | yes | seconds | Lap time of the reference lap. |
| `comparisonLapTimeSeconds` | number | yes | seconds | Lap time of the compared lap. |
| `totalDeltaSeconds` | number | yes | seconds | `comparisonLapTimeSeconds - referenceLapTimeSeconds`. |
| `deltaTrace` | `LapDeltaPoint[]` | yes | none | Full-lap interpolated delta graph data. |
| `cornerComparisons` | `CornerComparison[]` | yes | none | Time/speed/input differences per corner. |
| `sectorComparisons` | `SectorComparison[]` | yes | none | Time differences per sector. |
| `isValid` | boolean | yes | boolean | Whether this comparison should be trusted. |
| `invalidReasons` | string[] | yes | none | Reasons this comparison is invalid. Empty when valid. |
| `summary` | `LapComparisonSummary` | yes | none | Quick UI/debug summary. |

---

## 19. LapDeltaPoint

`LapDeltaPoint` is one point in the full-lap delta trace.

It compares both laps at the same `lapDistPct`, not at the same timestamp.

| Field | Type | Required | Unit/scale | Contains / represents |
|---|---:|---:|---:|---|
| `lapDistPct` | number | yes | 0–1 fraction | Track position where both laps were compared. |
| `referenceElapsedTimeSeconds` | number | yes | seconds | Reference lap elapsed time at this position. |
| `comparisonElapsedTimeSeconds` | number | yes | seconds | Comparison lap elapsed time at this position. |
| `deltaSeconds` | number | yes | seconds | `comparisonElapsedTimeSeconds - referenceElapsedTimeSeconds`. |
| `referenceSpeedMetersPerSecond` | number/null | yes | m/s | Reference lap speed at this position. |
| `comparisonSpeedMetersPerSecond` | number/null | yes | m/s | Comparison lap speed at this position. |
| `speedDeltaMetersPerSecond` | number/null | yes | m/s | `comparisonSpeed - referenceSpeed`. |
| `referenceThrottle` | number/null | yes | 0–1 | Reference lap throttle at this position. |
| `comparisonThrottle` | number/null | yes | 0–1 | Comparison lap throttle at this position. |
| `throttleDelta` | number/null | yes | 0–1 | `comparisonThrottle - referenceThrottle`. |
| `referenceBrake` | number/null | yes | 0–1 | Reference lap brake at this position. |
| `comparisonBrake` | number/null | yes | 0–1 | Comparison lap brake at this position. |
| `brakeDelta` | number/null | yes | 0–1 | `comparisonBrake - referenceBrake`. |

---

## 20. CornerComparison

`CornerComparison` compares two laps through one static corner.

| Field | Type | Required | Unit/scale | Contains / represents |
|---|---:|---:|---:|---|
| `cornerId` | number | yes | none | Static corner being compared. |
| `startDistPct` | number | yes | 0–1 fraction | Corner start used for comparison. |
| `endDistPct` | number | yes | 0–1 fraction | Corner end used for comparison. |
| `referenceEntrySpeedMetersPerSecond` | number/null | yes | m/s | Reference lap entry speed. |
| `comparisonEntrySpeedMetersPerSecond` | number/null | yes | m/s | Comparison lap entry speed. |
| `entrySpeedDeltaMetersPerSecond` | number/null | yes | m/s | `comparisonEntrySpeed - referenceEntrySpeed`. |
| `referenceMinSpeedMetersPerSecond` | number/null | yes | m/s | Reference lap minimum corner speed. |
| `comparisonMinSpeedMetersPerSecond` | number/null | yes | m/s | Comparison lap minimum corner speed. |
| `minSpeedDeltaMetersPerSecond` | number/null | yes | m/s | `comparisonMinSpeed - referenceMinSpeed`. |
| `referenceExitSpeedMetersPerSecond` | number/null | yes | m/s | Reference lap exit speed. |
| `comparisonExitSpeedMetersPerSecond` | number/null | yes | m/s | Comparison lap exit speed. |
| `exitSpeedDeltaMetersPerSecond` | number/null | yes | m/s | `comparisonExitSpeed - referenceExitSpeed`. |
| `referenceBrakeStartDistPct` | number/null | yes | 0–1 fraction | Reference lap brake start point. |
| `comparisonBrakeStartDistPct` | number/null | yes | 0–1 fraction | Comparison lap brake start point. |
| `brakeStartDeltaDistPct` | number/null | yes | 0–1 fraction | Difference between braking start points. |
| `referenceThrottlePickupDistPct` | number/null | yes | 0–1 fraction | Reference lap throttle pickup point. |
| `comparisonThrottlePickupDistPct` | number/null | yes | 0–1 fraction | Comparison lap throttle pickup point. |
| `throttlePickupDeltaDistPct` | number/null | yes | 0–1 fraction | Difference between throttle pickup points. |
| `timeDeltaSeconds` | number/null | yes | seconds | Time lost/gained through this corner using the global sign convention. |
| `isValid` | boolean | yes | boolean | Whether this corner comparison should be trusted. |
| `invalidReasons` | string[] | yes | none | Reasons this comparison is invalid. Empty when valid. |

---

## 21. SectorComparison

`SectorComparison` compares two laps through one static sector.

| Field | Type | Required | Unit | Contains / represents |
|---|---:|---:|---:|---|
| `sectorId` | number | yes | none | Static sector being compared. |
| `startDistPct` | number | yes | 0–1 fraction | Sector start used for comparison. |
| `endDistPct` | number | yes | 0–1 fraction | Derived sector end used for comparison. |
| `referenceSectorTimeSeconds` | number/null | yes | seconds | Reference lap sector time. |
| `comparisonSectorTimeSeconds` | number/null | yes | seconds | Comparison lap sector time. |
| `sectorDeltaSeconds` | number/null | yes | seconds | `comparisonSectorTimeSeconds - referenceSectorTimeSeconds`. |
| `isValid` | boolean | yes | boolean | Whether this sector comparison should be trusted. |
| `invalidReasons` | string[] | yes | none | Reasons this comparison is invalid. Empty when valid. |

---

## 22. LapComparisonSummary

`LapComparisonSummary` provides quick UI/debug highlights for a comparison.

| Field | Type | Required | Unit/scale | Contains / represents |
|---|---:|---:|---:|---|
| `biggestGainCornerId` | number/null | yes | none | Corner where comparison lap gained the most time. |
| `biggestGainSeconds` | number/null | yes | seconds | Most negative corner delta. |
| `biggestLossCornerId` | number/null | yes | none | Corner where comparison lap lost the most time. |
| `biggestLossSeconds` | number/null | yes | seconds | Most positive corner delta. |
| `biggestGainSectorId` | number/null | yes | none | Sector where comparison lap gained the most time. |
| `biggestGainSectorSeconds` | number/null | yes | seconds | Most negative sector delta. |
| `biggestLossSectorId` | number/null | yes | none | Sector where comparison lap lost the most time. |
| `biggestLossSectorSeconds` | number/null | yes | seconds | Most positive sector delta. |
| `maxSpeedDeltaMetersPerSecond` | number/null | yes | m/s | Largest speed difference found in delta trace. |
| `maxBrakeDelta` | number/null | yes | 0–1 | Largest brake difference found in delta trace. |
| `maxThrottleDelta` | number/null | yes | 0–1 | Largest throttle difference found in delta trace. |

---

## 23. Current okayama.json migration notes

The current generated Okayama file should eventually be migrated to this schema.

Required cleanup:

| Current field | Final field |
|---|---|
| `track.name: "okayama"` | `track.name: "Okayama International Circuit"` |
| missing | `track.trackId: 166` |
| missing | `track.configName: "Full Course"` |
| missing | `track.slug: "okayama-full-course"` |
| `track.generatedAt` | `generation.generatedAt` |
| `track.origin.lat` | `coordinateSystem.originLat` |
| `track.origin.lon` | `coordinateSystem.originLon` |
| `track.pointCount` | `generation.pointCount` |
| `track.trackLength` | `track.trackLengthMeters` |
| `left` | `geometry.leftBoundary` |
| `right` | `geometry.rightBoundary` |
| `centerline` | `geometry.centerline` |
| point `distance` | point `distanceMeters` |
| point `width` | point `widthMeters` |
| corner `maxCurvature` | corner `maxCurvatureDegPerMeter` |
| sector `endDistPct` | remove from stored `TrackModel`; derive in code |

---

## 24. Known follow-up checks

Before implementing all logic against this document, confirm the following from `.ibt` variable metadata:

- exact unit for `YawRate`
- exact unit for `LatAccel`
- exact unit for `LongAccel`
- exact type/meaning of `PlayerTrackSurface`
- whether `TrackID` alone is always sufficient for matching layouts, or whether `trackId + configName` is needed for some tracks

These checks should not block the v1 document, but they should be resolved before relying on those fields in deeper analysis.

---

## 25. Implementation rule of thumb

When adding any new field, ask:

1. Is this raw iRacing data, normalized parsed data, static track data, or derived analysis?
2. Does an equivalent field already exist under another name?
3. Does the field name include the unit if needed?
4. Is this per-sample, per-lap, per-session, per-corner, or per-comparison?
5. Does this belong in `TrackModel`, `Session`, `Lap`, `LapAnalysis`, or `LapComparison`?

If the answer is unclear, do not add the field until the model boundary is clear.
