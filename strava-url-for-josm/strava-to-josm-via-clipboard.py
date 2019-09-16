import clipboard
import json


try:
    d = clipboard.paste()
    print("Read from clipboard:")
    print("-----")
    print(d)
    print("-----")
    d = json.loads(d)['Request cookies']
except:
    print()
    print("Please 'Copy All' on the Network>Cookies on a logged in strava request for heatmap....")
    print()
    exit(1)

url = 'tms[3,15]:https://heatmap-external-b.strava.com/tiles-auth/run/hot/{zoom}/{x}/{y}.png?v=19&'+f'Key-Pair-Id={d["CloudFront-Key-Pair-Id"]}&Signature={d["CloudFront-Signature"]}&Policy={d["CloudFront-Policy"]}'
print("Copying to clipboard")
print("-----")
print(url)
print("-----")
clipboard.copy(url)
