import streamlit as st
import pickle
import pandas as pd
import numpy as np
import requests

# Configure the page
st.set_page_config(
    page_title="Movie Recommender System",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .movie-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .movie-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #333;
    }
    .recommendation-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        movies_dict = pickle.load(open('movie_list.pkl', 'rb'))
        movies = pd.DataFrame(movies_dict)

        similarity = pickle.load(open('similarity.pkl', 'rb'))
        return movies, similarity
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None

@st.cache_data
def fetch_poster(movie_id):
    try:
        
        api_key = st.secrets["api"]
        
        response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US")
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500/{poster_path}"
        else:
            return "https://via.placeholder.com/500x750?text=No+Poster+Available"
    except:
        return "https://via.placeholder.com/500x750?text=No+Poster+Available"

def recommend_movies(movie, movies, similarity):
    try:
        movie_index = movies[movies['title'] == movie].index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
        recommended_movies = []
        for i in movies_list:
            movie_data = movies.iloc[i[0]]
            recommended_movies.append({
                'title': movie_data.title,
                'movie_id': movie_data.movie_id,
                'similarity_score': round(i[1], 3)
            })
        return recommended_movies
    except:
        return []

def display_list_view(recommendations):
    with st.expander("📜 View as List (Vertical)"):
        for i, movie in enumerate(recommendations, 1):
            poster_url = fetch_poster(movie['movie_id'])
            col_poster, col_info = st.columns([1, 3])
            with col_poster:
                st.image(poster_url, width=100)
            with col_info:
                st.markdown(f"""
                <div style="padding: 10px;">
                    <div style="font-weight: bold; font-size: 1.1rem; color: #333;">
                        {i}. {movie['title']}
                    </div>
                    <div style="color: #666; font-size: 0.9rem;">
                        Similarity Score: {movie['similarity_score']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

def main():
    st.markdown('<div class="main-header">🎮 Movie Recommender System</div>', unsafe_allow_html=True)
    movies, similarity = load_data()

    if movies is None or similarity is None:
        st.stop()

    col1, col2 = st.columns([1, 2])

    with st.sidebar:
        st.header("About")
        st.write("""
        Movie Recommender System .
        """)
        st.metric("Total Movies", len(movies))
        st.metric("Features Used", "5000")

    with col1:
        st.subheader("Select a Movie")
        selected_movie = st.selectbox("Choose a movie you liked:", movies['title'].values, index=0)
        search_query = st.text_input("Or search for a movie:")
        if search_query:
            filtered_movies = movies[movies['title'].str.contains(search_query, case=False, na=False)]
            if not filtered_movies.empty:
                selected_movie = st.selectbox("Search results:", filtered_movies['title'].values, key="search_results")

        if st.button("Get Recommendations", type="primary"):
            st.session_state.get_recommendations = True
            st.session_state.selected_movie = selected_movie

    with col2:
        st.subheader("Movie Recommendations")
        if hasattr(st.session_state, 'get_recommendations') and st.session_state.get_recommendations:
            with st.spinner("Finding similar movies..."):
                recommendations = recommend_movies(st.session_state.selected_movie, movies, similarity)

            if recommendations:
                st.success(f"Movies similar to **{st.session_state.selected_movie}**:")
                cols = st.columns(3)
                for i, movie in enumerate(recommendations):
                    with cols[i % 3]:
                        poster_url = fetch_poster(movie['movie_id'])
                        st.image(poster_url )
                        st.markdown(f"""
                        <div style="text-align:center;">
                            <strong>{movie['title']}</strong><br/>
                            <span style="color: #666;">Similarity: {movie['similarity_score']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                with col1:
                    display_list_view(recommendations)
                # with col2:
                #     display_list_view(recommendations)
            else:
                st.warning("No recommendations found for this movie.")
        else:
            st.info("👇 Select a movie and click 'Get Recommendations' to see suggestions!")

    if selected_movie:
        with st.sidebar:
            st.markdown("---")
            st.subheader("Selected Movie")
            try:
                movie_data = movies[movies['title'] == selected_movie].iloc[0]
                poster_url = fetch_poster(movie_data.movie_id)
                st.image(poster_url)
                st.write(f"**{selected_movie}**")
            except:
                st.write(f"**{selected_movie}**")

    st.markdown("---")
    with st.expander("🎲 Discover Random Movies"):
        if st.button("Show Random Movies"):
            random_movies = movies.sample(6)
            st.subheader("Random Movie Collection")
            cols = st.columns(3)
            for i, (_, movie) in enumerate(random_movies.iterrows()):
                with cols[i % 3]:
                    poster_url = fetch_poster(movie['movie_id'])
                    st.image(poster_url)
                    st.markdown(f"""
                    <div style="text-align: center; margin-top: 10px;">
                        <div style="font-weight: bold; font-size: 1rem; color: #333;">
                            {movie['title']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Get Recommendations", key=f"random_{i}"):
                        st.session_state.get_recommendations = True
                        st.session_state.selected_movie = movie['title']
                        st.experimental_rerun()

    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8rem;'>
         Content-Based Movie Recommender
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
