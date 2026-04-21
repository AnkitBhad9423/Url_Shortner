# app/utils.py

BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def encode_base62(num: int) -> str:
    """Convert an integer ID to a Base62 short code"""
    if num == 0:
        return BASE62[0]
    
    result = []
    while num:
        result.append(BASE62[num % 62])
        num //= 62
    
    return "".join(reversed(result))


# Quick test — run this file directly to verify
if __name__ == "__main__":
    for i in [1, 100, 999, 125000, 9999999]:
        print(f"{i:>10} → {encode_base62(i)}")