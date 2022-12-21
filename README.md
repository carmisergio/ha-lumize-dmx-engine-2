# HomeAssistant Lumize DMX Engine 2

HomeAssistant integration for the Lumize Switch Controller 2

## Installation

Copy the entire `ldmxe2` directory into your `custom_components` directory inside your HomeAssistant configuration folder.
Reboot HomeAssistant and continue with [Configuration](##Configuration)

## Configuration

### Platform config

Inside your `configuration.yaml` file, add the following required platform configuration:

```yaml
ldmxe2:
  host: <IP address>
```

Configuration parameters:

- `host` (required): IP address of the device running LDMXE2.
- `port` (optional): port the LDMXE2 is configured to. (default = 8056)
- `keep_alive` (optional): seconds between a keep alive message sent to the Engine and the next. 0 to disable keep alive entirely. (default = 0)

### Lights config

Then, add the following config to your `lights:` configuration for every channel of the Engine you want to control:

```yaml
- platform: ldmxe2
  name: "LDMXE2 Light Channel 0"
  channel: 0
```

Configuration parameters:

- `name` (required): Friendly name of the light entity.
- `channel` (required): channel on the Engine this light is connected to.

## Services

The integration will provide two services:

- `ldmxe2.dim_start`
- `ldmxe2.dim_stop`

They allow easy starting and stopping of a pushbutton fade on a specific light.

### Usage

Just call the service and pass it the `entity_id` of the light you want to dim
