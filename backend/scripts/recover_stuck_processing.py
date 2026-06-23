"""
Recupera mensajes atascados en estado 'procesando' (worker crasheado mid-tick).

  cd backend && python scripts/recover_stuck_processing.py
  cd backend && python scripts/recover_stuck_processing.py --minutes 45
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.queue_maintenance import recover_stuck_processing
from src.tools.supabase_client import db_client


async def main(stale_minutes: int | None) -> None:
    await db_client.connect()
    try:
        count = await recover_stuck_processing(stale_minutes)
        print(f"Recuperados: {count} mensaje(s) en procesando → pendiente")
    finally:
        await db_client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recuperar feedback_raw atascado en procesando")
    parser.add_argument(
        "--minutes",
        type=int,
        default=None,
        help="Antigüedad mínima en minutos (default: STUCK_PROCESSING_MINUTES)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.minutes))
