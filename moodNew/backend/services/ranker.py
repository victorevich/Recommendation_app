import numpy as np


class Ranker:
    def rank(self, candidates, query_vec, session_centroid=None,
             global_centroid=None, alpha=0.5, beta=0.6, gamma=0.3, delta=0.1):

        if session_centroid and global_centroid:
            user_vec = alpha * np.array(session_centroid) + (1 - alpha) * np.array(global_centroid)
        elif session_centroid:
            user_vec = np.array(session_centroid)
        elif global_centroid:
            user_vec = np.array(global_centroid)
        else:
            user_vec = None

        for item in candidates:
            ep_vec = np.array(item["embedding"])
            cos_q = _cosine(query_vec, ep_vec)
            imdb = (item["imdb_rating"] - 1) / 9

            if user_vec is not None:
                cos_u = _cosine(user_vec, ep_vec)
                score = beta * cos_q + gamma * cos_u + delta * imdb
            else:
                score = (beta + gamma) * cos_q + delta * imdb

            item["score"] = round(score * 100)

        return sorted(candidates, key=lambda x: x["score"], reverse=True)


def _cosine(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom > 0 else 0.0