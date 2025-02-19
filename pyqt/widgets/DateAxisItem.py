from datetime import datetime, timezone

from pyqtgraph import AxisItem


class DateAxisItem(AxisItem):
    def tickStrings(self, values, scale, spacing):
        formatted_ticks = []
        for value in values:
            try:
                if value < 0 or value > 32503680000:
                    formatted_ticks.append("")
                    continue

                dt = datetime.fromtimestamp(value, tz=timezone.utc)

                if spacing < 3600:
                    formatted_ticks.append(dt.strftime('%H:%M:%S'))
                elif spacing < 86400:
                    formatted_ticks.append(dt.strftime('%d %B %H:%M'))
                else:
                    formatted_ticks.append(dt.strftime('%d %B'))
            except Exception as e:
                formatted_ticks.append("")
        return formatted_ticks
