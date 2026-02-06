#!/usr/bin/env python3
from datetime import datetime
now = datetime.now()
print(f"📅 Data atual: {now.strftime('%d/%m/%Y')} ({now.strftime('%Y-%m-%d')}) | Ano: {now.year} | Hora: {now.strftime('%H:%M')}")
