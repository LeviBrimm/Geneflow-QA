from app.services.similarity import cosine_similarity, embed_text, vector_from_storage, vector_to_storage


def test_vector_storage_round_trip():
    vector = [1.0, 2.5, 3.25]
    assert vector_from_storage(vector_to_storage(vector)) == vector


def test_cosine_similarity_scores_identical_vectors_highest():
    vector = embed_text("pathogenic variant domain")
    assert cosine_similarity(vector, vector) == 1.0
