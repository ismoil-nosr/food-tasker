from datetime import datetime, timedelta

today = datetime.now()
current_weekdays = (
    today +
    timedelta(
        days=i) for i in range(
        0 -
        today.weekday(),
        7 -
        today.weekday()))
print(today)
print("######################################")
for x in current_weekdays:
    print(x.day)
