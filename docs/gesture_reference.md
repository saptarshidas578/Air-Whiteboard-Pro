# Gesture Controls & Vision Pipeline Specification

## MediaPipe Hands Landmark Geometry
- Tracks 21 3D hand keypoints (0 = Wrist, 4 = Thumb tip, 8 = Index tip, 12 = Middle tip, 16 = Ring tip, 20 = Pinky tip).
- Finger extension boolean evaluated by comparing tip Y position against PIP (proximal interphalangeal) joint Y position.

## State Transitions
```
                +---------------------------------------+
                |                                       |
                v                                       |
             [ IDLE ] --(Index Up, others folded)--> [ DRAW ]
                |                                       |
  (All Open)    |                                       | (Pinch Thumb+Index)
                v                                       v
            [ ERASE ]                              [ RESIZE ]
```

## Coordinate Smoothing
- Exponential Moving Average (EMA) applied to index fingertip coordinates:
  $$x_{\text{smooth}} = \alpha \cdot x_{\text{curr}} + (1 - \alpha) \cdot x_{\text{prev}}$$
  Eliminates micro-tremors and creates clean vector paths.
