# Moving Intelligence Device Tracker Component
This integration supports Moving Intelligence objects as device tracker in Home Assistant

NOTE: You need an account and api-key for https://movingintelligence.com/

## Installation

### HACS - Recommended
- Have [HACS](https://hacs.xyz) installed, this will allow you to easily manage and track updates.
- Add this repo to your HACS installation.
- Search for 'Moving Intelligence'.
- Click Install below the found integration.
- Configure using the configuration instructions below.
- Restart Home-Assistant.

### Manual
- Copy directory `custom_components/moving_intelligence` to your `<config dir>/custom_components` directory.
- Configure with config below.
- Restart Home-Assistant.

## Usage
To use this component in your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry

device_tracker:
  - platform: moving_intelligence
    username: <your email address>
    api_key: <your api-key for moving-intelligence>
    include:
       - LICENSEPLATE1
       - LICENSEPLATE2
```

Configuration variables:

- **username** (*Required*): The email address used for your https://movingintelligence.com/ account
- **api_key** (*Required*): The email api-key used for your https://movingintelligence.com/ account
- **include** (*Optional*): A list of license plates to track, if not supplied all objects are tracked

You can give the devices friendly names like so:

```
homeassistant:
  customize:
    device_tracker.g001bb:
      friendly_name: "Porsche 718 Cayman"
      icon: mdi:car
    device_tracker.g002bb:
      friendly_name: "Tesla Cybertruck"
      icon: mdi:car
```
