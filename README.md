
*pizzaagent* receives an audio stream from a supposed phone caller and issues calls to Deliver24 to order food according to customer requirement.
The project was during a hackathon of KI-Netzwerk Dresden (https://ki-dresden.net/).

The pizzaagent is started using `pipecat/server.py`. A `.env` file in the `pipecat` directory configures:
* `LLM_API_URL` connecting to an OpenAPI compatible LLM using `LLM_API_KEY`
* `STT_API_URL` connects to a Whisper instance using key `STT_API_KEY`
* `TTS_API_URL` connects to a text-to-speech instance using key `TTS_API_KEY`

The tool calling is implemented using `FastMCP` in `shop_connector.py`.
