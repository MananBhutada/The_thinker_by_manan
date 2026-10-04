"""English automatic mode routing."""
MODE_NAMES={"auto":"Auto","rational":"Reason","random":"Random","nature":"Nature","dialogue":"Dialogue","fengshui":"Traditional"}
RULES=[("random",["what should i eat","what should i watch","where should i go","lunch","dinner","breakfast"]),("fengshui",["bazi","fortune","feng shui","astrology","horoscope"]),("rational",["quit","job","career","buy a house","rent","startup","invest","loan","car","study"]),("dialogue",["afraid","scared","stuck","hesitant","should i tell","what should i say"]),("nature",["relationship","love","dating","breakup","marriage","travel"]),("rational",["book","buy","sell","switch","keep or"])]
def explain(question:str)->dict:
 q=(question or "").strip().lower()
 for mode,keys in RULES:
  for k in keys:
   if k in q:return {"mode":mode,"reason":f'Matched "{k}"; routed to {MODE_NAMES[mode]} mode',"confidence":76}
 return {"mode":"rational","reason":"No specific scenario matched; using Reason mode","confidence":52}
def recognize(question:str)->str:return explain(question)["mode"]
