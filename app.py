import streamlit as st
import pandas as pd
from wordnet_utils import load_wordnet, load_index, explore_word

# Load once
DATA_FILES = ["data/data.noun", "data/data.verb", "data/data.adj", "data/data.adv"]
INDEX_FILES = ["data/index.noun", "data/index.verb", "data/index.adj", "data/index.adv"]

st.title("🌐 WordNet Explorer")

@st.cache_data
def load_all():
    df = load_wordnet(DATA_FILES)
    index_dict = load_index(INDEX_FILES)
    return df, index_dict

df, index_dict = load_all()

word = st.text_input("",placeholder="Search for a word...",icon="🔎")
if word:
    st.write(f"Results for **{word}**:")
    results = explore_word(df, index_dict, word)
    for res in results:
        st.markdown(res)
