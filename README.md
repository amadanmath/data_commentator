# Data Commentator

Data Commentator is a modular framework that facilitates creating audio commentary from a datastream. It is data-agnostic, and is meant to be used as a base where custom components can be plugged in; mainly, payload enhancer, priority predictor and predictor components, as well as the overlay frontend.

## Data Flow

The data flow in a pipeline, as follows:

* **Data source** (automatic): typically a webserver accepting data payloads as JSON POST requests. It is also possible to capture the data in a JSONL file, and replay it later.
* **Payload enhancer** (optional): a component that modifies the existing features, or adds new ones to the payload. By default, the payload is unchanged.
* **Priority predictor** (optional): a component that predicts how important it is to comment at the current timepoint. A comment with a higher priority will cut off a comment with a lower priority. A priority of 0 indicates the current data is not worth commenting. To avoid duplicate calculation, priority predictor can pass extra data context to the predictor. By default, the priority is always 1, resulting in comments being generated as soon as possible without overlapping.
* **Predictor** (mandatory): a component that turns the data into a natural-language comment string. Data is aggregated into a window of a configurable size and sampling frequency before being passed to the predictor.
* **Synthesizer** (optional): a Text-To-Speech component. Several TTS engines are supported out of the box.
* **Speaker** (default): a component that plays the generated audio clip and/or displays the generated text. By default it plays directly on the system where Data Commentator is running, but it can also send it to the embedded webserver, which will send it to a page that can be loaded as an overlay in e.g. [OBS Studio](https://obsproject.com/). The overlay frontend is not included, as it needs to be tailored to the data.


## Building

Since this package is not yet published to PyPI, you will have to build and install it manually:

```
python3 -m pip install --upgrade build
python3 -m build
python3 -m pip install -e .
```

## Running 

You can start Data Commentator with

```
data-commentator
```

By default, Data Commentator reads the config file `config.toml`. Some of the options can be overridden in command line; some can only be set from the config file. `-c`/`--config` parameter can be used to select an alternate config file.
