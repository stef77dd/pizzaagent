#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#
import os
import sys

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer, VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.openai import OpenAILLMService, OpenAISTTService, OpenAITTSService
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport

load_dotenv(override=True)

SYSTEM_INSTRUCTION = f"""
You are Realtime Voice Chatbot, a friendly and helpful robot.
Your goal is to demonstrate your capabilities concisely.
Your output will be converted to audio, so you should not use special characters or emojis in your responses.
Respond to what the user has said in a creative and helpful way. Keep your answers short. At most one or two sentences.
"""


async def run_bot(webrtc_connection):
    pipecat_transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.5)),
            audio_out_10ms_chunks=2,
        ),
    )

    # Configure service
    stt = OpenAISTTService(
        model="faster-whisper-large-v3",
        api_key=os.getenv("STT_API_KEY"),
        base_url=os.getenv("STT_API_URL"),
        language="en",
        #prompt="Transcribe technical terms accurately. Format numbers as digits rather than words."
    )

    llm = OpenAILLMService(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_API_URL"),
        model="gemma3:4b"#"gemma-3-4b-it-qat-q4_0"
    )

    # # Configure service
    # tts = OpenAITTSService(
    #     voice="nova",
    #     model="gpt-4o-mini-tts",
    #     base_url=os.getenv("OPENAI_API_URL"),
    #     api_key=os.getenv("OPENAI_API_KEY"),
    # )
    # Configure service
    tts = OpenAITTSService(
        #voice="echo",
        model="cosyvoice-300m-sft",
        base_url=os.getenv("TTS_API_URL"),
        api_key=os.getenv("TTS_API_KEY"),
    )

    context = OpenAILLMContext(
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": "Start by greeting the user."},
        ],
    )
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline(
        [
            pipecat_transport.input(),
            stt,
            context_aggregator.user(),
            llm,  # LLM
            tts,
            pipecat_transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
        ),
    )

    @pipecat_transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Pipecat Client connected")
        # Kick off the conversation.
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @pipecat_transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Pipecat Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)

    await runner.run(task)
