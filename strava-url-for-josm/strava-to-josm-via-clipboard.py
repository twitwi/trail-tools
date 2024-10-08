import clipboard
import json


try:
    d = clipboard.paste()
    print("Read from clipboard:")
    print("-----")
    print(d)
    print("-----")
    d = json.loads(d)
    if len(d.keys()) == 1:
        d = d[list(d.keys())[0]]
    elif 'Request cookies' in d:
        d = d['Request cookies']
    elif 'CloudFront-Policy' in d:
        d = d # ok
    else:
        print('Probably a problem')
except Exception as e:
    print(e)
    print("-------------------")
    print("-------------------")
    print("Please 'Copy All' on the Network>Cookies on a logged in strava request for heatmap....")
    print()
    exit(1)

url = 'tms[3,15]:https://heatmap-external-b.strava.com/tiles-auth/run/hot/{zoom}/{x}/{y}.png?v=19&'+f'Key-Pair-Id={d["CloudFront-Key-Pair-Id"]}&Signature={d["CloudFront-Signature"]}&Policy={d["CloudFront-Policy"]}'
print("-------------------")
print("Use this for josm:")
print("-------------------")
print(url)
print("-------------------")
url = 'https://heatmap-external-b.strava.com/tiles-auth/run/hot/{z}/{x}/{y}.png?v=19&'+f'Key-Pair-Id={d["CloudFront-Key-Pair-Id"]}&Signature={d["CloudFront-Signature"]}&Policy={d["CloudFront-Policy"]}'
print("Copying to clipboard (for brouter)")
print("-----")
print(url)
print("-----")
clipboard.copy(url)
