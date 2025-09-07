from enum import Enum


class VectorDBEnums(Enum):

    QDRANT = "qdrant"

class DistanceMethodEnums(Enum):
    
    COSINE = "Cosine"
    EUCLIDEAN = "Euclidean"
    DOT = "Dot"