from typing import List

import numpy as np


def cosine_similarity(a: List[float], b: List[float]) -> float:
    a_arr, b_arr = np.array(a), np.array(b)
    denom = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if denom == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / denom)


def top_similar(query_embedding: List[float], notes: List[dict], top_k: int = 5) -> List[str]:
    scored = [(cosine_similarity(query_embedding, n["embedding"]), n["text"]) for n in notes]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [text for _, text in scored[:top_k]]
