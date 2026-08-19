from datetime import datetime, timezone

from pyqtgraph import AxisItem


class DateAxisItem(AxisItem):
    def tickStrings(self, values, scale, spacing):
        formatted_ticks = []
        local_tz = get_timezone()

        for value in values:
            try:
                if value < 0 or value > 32503680000:
                    formatted_ticks.append("")
                    continue

                dt = datetime.fromtimestamp(value, tz=local_tz)

                if spacing < 3600:
                    formatted_ticks.append(dt.strftime('%H:%M:%S'))
                elif spacing < 86400:
                    formatted_ticks.append(dt.strftime('%d %b %H:%M'))
                else:
                    formatted_ticks.append(dt.strftime('%d %b'))
            except Exception:
                formatted_ticks.append("")
        return formatted_ticks