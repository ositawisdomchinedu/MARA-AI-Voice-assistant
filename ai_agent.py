import logging
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, JobContext, RoomInputOptions
from livekit.plugins import (
    groq, elevenlabs, noise_cancellation,
    cartesia, silero
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from prompts import AGENT_INSTRUCTIONS, SESSION_INSTRUCTIONS
from tools import (
    get_weather, search_web, send_email, calculate, get_current_time,
    book_appointment, list_appointments, delete_appointment,
    add_task, list_tasks, remove_task
)

load_dotenv()
logger = logging.getLogger("livekit-agent")

WAKE_WORD = "mara"

class TriggeredAgentSession(AgentSession):
    async def on_user_utterance(self, utterance: str):
        print(f"[Voice Input] {utterance}")
        if utterance.strip().lower().startswith(WAKE_WORD):
            cleaned = utterance[len(WAKE_WORD):].strip(" ,:")
            print(f"[Triggered] '{cleaned}'")
            return await super().on_user_utterance(cleaned)
        else:
            print("[Ignored] Wake word not detected.")
            return


class Assistant(Agent):
    def __init__(self) -> None:
        agent_tools = [
            get_weather, search_web, send_email, calculate, get_current_time,
            book_appointment, list_appointments, delete_appointment,
            add_task, list_tasks, remove_task
        ]

        print("Tools registered in Assistant:", [tool.__name__ for tool in agent_tools])

        super().__init__(
            instructions=AGENT_INSTRUCTIONS,
            tools=agent_tools,
            stt=cartesia.STT(model="ink-whisper"),
            # tts=elevenlabs.TTS(voice_id="ODq5zmih8GrVes37Dizd", model="eleven_multilingual_v2"),
            tts=cartesia.TTS(model="sonic-2", voice="bf0a246a-8642-498a-9950-80c35e9276b5"),
            llm=groq.LLM(model="llama-3.3-70b-versatile", temperature=0.4)
        )


async def entrypoint(ctx: JobContext):
    session = TriggeredAgentSession(
        vad=silero.VAD.load(),
        #turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC()
        ),
    )

    await ctx.connect()

    await session.generate_reply(instructions=SESSION_INSTRUCTIONS)


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
