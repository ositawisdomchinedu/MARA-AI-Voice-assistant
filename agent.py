from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    groq,
    cartesia,
    elevenlabs,
    deepgram,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from prompts import AGENT_INSTRUCTIONS, SESSION_INSTRUCTIONS
from tools import (
    get_weather, search_web, send_email, calculate, get_current_time,
    book_appointment, list_appointments, delete_appointment,
    add_task, list_tasks, remove_task
)

load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:

        agent_tools = [
            get_weather, search_web, send_email, calculate, get_current_time,
            book_appointment, list_appointments, delete_appointment,
            add_task, list_tasks, remove_task
        ]

        print("Tools registered in Assistant:", [tool.__name__ for tool in agent_tools])

        super().__init__(instructions=AGENT_INSTRUCTIONS)


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        #stt=deepgram.STT(model="nova-3", language="multi"),
        stt=cartesia.STT(model="ink-whisper"),
        llm=groq.LLM(model="llama-3.3-70b-versatile", temperature=0.4),
        #tts=elevenlabs.TTS(voice_id="yj30vwTGJxSHezdAGsv9", model="eleven_multilingual_v2"),
        tts=cartesia.TTS(model="sonic-2", voice="bf0a246a-8642-498a-9950-80c35e9276b5"),
        vad=silero.VAD.load(),
        #turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions=SESSION_INSTRUCTIONS
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))