from hashlib import sha1
from .data_models import Claim, VerificationStatus

def extract_claims_heuristic(texts):
    # Conservative fallback: do not label claims as verified based on extraction alone.
    claims=[]
    for text in texts:
        for sentence in text.replace('\n',' ').split('. '):
            s=sentence.strip(' .\n')
            if len(s.split())>=6 and any(v in s.lower().split() for v in ('announced','said','reported','approved','launched','published','confirmed','increased','decreased','won','signed')):
                claims.append(Claim(claim_id=sha1(s.encode()).hexdigest()[:10],text=s,status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                                    limitations=['Heuristic claim candidate; needs evidence review.']))
    unique={c.text:c for c in claims}
    return list(unique.values())[:20]
