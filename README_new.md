# WaveMaker - Fall 2024

## Summary
Team P Fall 2025 - We have enchanced the WaveMaker platform with real-time motor control capabilities, allowing clients to start/stop motors, modify parameters, and load presets on the fly without restarting the system.

---

## Getting Started

### Prerequisites
- Python 3.8 or higher

### Installation & Running
```bash
pip install -r requirements.txt
python main.py
```

---

## Files Edited
Below files were modified to implement the new features:
- `Model.py`
- `Motor.py`
- `View.py`
- `ControlHome.py`
- `DefineMotors.py`
- `PresetOptions.py`
- `PresetProcessor.py`

---

## Contributions
We received the core structure of the platform and codebase from earlier teams who worked on this project. New files were not created; existing files were edited to maintain the same workflow and minimize changes as per client requirements.

- **Added functionality to stop and start the motors on the fly whenever needed** - Previously this required exiting and rehoming all the motors again. *(Pavan, Chidaksh)*

- **Added flexibility to change parameters and add motors during a run while ensuring they stay in-phase** *(Pavan, Tran)*

- **Figured out the units/metrics for each quantity** - Documentation for parameters. See [README_PARAMETER_REFERENCE.md](README_PARAMETER_REFERENCE.md) *(Tran)*

- **Complete Reset button for Motors and Parameters** - Reset on the fly without restarting the machine. *(Pavan)*

- **Loading preset configurations into the motors for reproducibility of waves** - Different presets can be loaded to different sets of motors for generating peculiar waves. *(Chidaksh, Shreyas)*

- **Added stop buttons in the Define Motors tab** - More flexibility; no need to change tabs to stop the motors. *(Chidaksh)*

---

## Current Limitations
- Can't set different parameters for individual motors manually (only possible with presets)
- Can't change parameters without stopping the motors while running
- Can't load a different preset while the motor is up and running

---

## Reference Videos

### Final Presentation
[Final Presentation](https://drive.google.com/file/d/1eVHyr6L9DJV12vwuuF3wHgS7B4bUvn91/view?usp=drive_link)

### Demo
[Demo](https://drive.google.com/file/d/1ksRIBGH2iqyl9qSDY-udTSy5llmQN6hU/view?usp=drive_link)

### Basic Working
[Basic Working](https://drive.google.com/file/d/1dc2NiC3NNdMMKORIJJ2DIuqR-n5qq2U_/view?usp=drive_link)

### How to Access the System
[How to Access the System](https://drive.google.com/file/d/17RTLjI5ECarjaRApMHN5sSI4J74el6go/view?usp=drive_link)

### Feature Videos

#### Stop Motors
[Stop Motors](https://drive.google.com/file/d/1N8Yr6jGKV4Oc_T6eRIpncp4G3uz5n5D_/view?usp=drive_link)

#### Adding Motors on the Fly
[Adding Motors on the Fly](https://drive.google.com/file/d/1FMVc0CpEGibEQMQpL1ltr9ZHg0gBe00N/view?usp=drive_link)

#### Complete Reset
[Complete Reset](https://drive.google.com/file/d/1xZrnarhHOohud0i73IiUMRg0lNJx7Ugq/view?usp=drive_link)

#### Loading Presets
[Loading Presets](https://drive.google.com/file/d/1W_7yLFRGhABVepfKtrNItr8uNGS5gdKo/view?usp=drive_link)

#### Different Presets for Different Set of Motors
[Different Presets for Different Set of Motors](https://drive.google.com/file/d/1ZivSKKuieuv3DP3UzBPh9CBcTRrGxKCT/view?usp=drive_link)
