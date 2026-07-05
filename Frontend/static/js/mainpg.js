let globalgenreForRecSp=''
let globalgenreForRecYt=''

const [nav] = performance.getEntriesByType("navigation");
if (nav && nav.type === "reload") {
    alert("Please Relogin!");
}
async function fetchGenres() {
  try {
    const response = await fetch('/basicRec', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const genreList = await response.json();
    console.log(genreList)
    return genreList; // Expecting it to be an array
  } catch (error) {
    console.error('Error fetching genres:', error);
    alert("Failed to fetch recommendations. Please try again later.");
    return [];
  }
}



window.addEventListener('load', async () => {
    const ytContainer = document.querySelector('.yt_recs');
    const spContainer = document.querySelector('.sp_recs');
    const imgPath = "/static/images/playlistimg.jpg";
    if (!ytContainer || !spContainer) {
        console.error("Containers not found");
        return;
    }

    const genres = await fetchGenres();

    genres.forEach(genre => {
        const ytCard = `<img src="${imgPath}" class="recommendation-card" data-genre="${genre}" data-platform="youtube" onclick="genreCardClick('${genre}', 'youtube')" />`;
        ytContainer.insertAdjacentHTML('beforeend', ytCard);
    });

    genres.forEach(genre => {
        const spCard = `<img src="${imgPath}" class="recommendation-card" data-genre="${genre}" data-platform="spotify" onclick="genreCardClick('${genre}', 'spotify')" />`;
        spContainer.insertAdjacentHTML('beforeend', spCard);
    });
});





let playYoutubeLink = `https://youtube.com`;
let playSpotifyLink = `https://spotify.com`;

function toggleMenu() {
  const submenu = document.getElementById("subMenu");
  submenu.classList.toggle("show");
  showProfile(event);
}
function toTitleCase(str) {
  return str
    .toLowerCase()
    .split(' ')
    .filter(word => word.trim() !== '') 
    .map(word => word[0].toUpperCase() + word.slice(1))
    .join(' ');
}

// Fetch request to search book
async function fetchBookData(bookName,filters) {
  // console.log({...filters,book:bookName});
  
  const queryParams = new URLSearchParams({...filters,book:bookName}) // To make it URL safe
  dataToSend={...filters,book:bookName}
  const url = `/bookEntry`;

  try {
    const response = await fetch(url,{
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(dataToSend)
    }); // API request
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json(); // Parse response as JSON
    console.log(data)
    return data;
  } catch (error) {
    console.error("Error during API call:", error);
    // document.getElementById("titleOfPage").value = bookName
    alert("Something went wrong. Please try again later")
  }
}

async function shufflePlaylist(bookName,filters,platform) {
  console.log({...filters,book:bookName});
  dataToSend={...filters,book:bookName,'platform':platform}

  try {
    const response = await fetch('/forward',{
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(dataToSend)
    }); // API request
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json(); // Parse response as JSON
    return data;
  } catch (error) {
    console.error("Error during API call:", error);
    // document.getElementById("titleOfPage").value = bookName
    alert("Something went wrong. Please try again later")
  }
}


async function playlistByGenreSelect(genre, platform) {
  try {
    const dataToSend = { genre: genre, platform: platform };
    console.log(dataToSend);
    
    const response = await fetch(`/fromRec`, {
      method: "POST",  // changed to POST
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(dataToSend)
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch playlist: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching playlist:", error);
  }
}



// API Call to search book
function searchBook(event){
    event.preventDefault(); // Stop page reload
  
    const input = document.getElementById("searchInputText");
    const bookName = input.value.trim();
    document.getElementById("titleOfPage").textContent=toTitleCase("This may take a while...");
    if (bookName === "") {
      alert("Please enter a book name to search.");
      return;
    }
  
    if (bookName === null || bookName.trim() === "") {
      alert("Search cancelled.");
      return;
    }
    const filters = getFilterValues();
    // Call API using Promise syntax
    let titleCaseBookName="This May Take While...";
    
    fetchBookData(bookName,filters)
      .then((result) => {
        console.log("Book data received:", result);
        playYoutubeLink=result.youtube
        playSpotifyLink=result.spotify
        // Optionally: update DOM here
        // loadRecents()
        const titleCaseBookName=toTitleCase(bookName);
        document.getElementById("titleOfPage").textContent=titleCaseBookName;
      })
      .catch((error) => {
        console.error("API call failed:", error);
        document.getElementById("titleOfPage").textContent=toTitleCase("Try Again Later");
        alert("Oops! Something went wrong while fetching book data.");
      });
      
      
}
// play button
function youtubePlayButton(event){
  event.preventDefault();

  if (playYoutubeLink) {
    window.open(playYoutubeLink, '_blank'); // Open in a new tab
  } else {
    alert("No YouTube link available to play.");
  }
}

function spotifyPlayButton(event){
  event.preventDefault();

  if (playSpotifyLink) {
    window.open(playSpotifyLink, '_blank'); // Open in a new tab
  } else {
    alert("No Spotify link available to play.");
  }

}

//Next button (Calls an API to fetch a playlist based on that book)

function playlist(event,platform){
  event.preventDefault(); // Stop page reload

  const input = document.getElementById("searchInputText");
  const bookName = input.value.trim();

  if (bookName === "") {
    alert("Please enter a book name to search.");
    return;
  }

  if (bookName === null || bookName.trim() === "") {
    alert("Search cancelled.");
    return;
  }

  document.getElementById("searchInputText").value = bookName
  const filters = getFilterValues();
  // Call API using Promise syntax
  shufflePlaylist(bookName,filters,platform)
    .then((result) => {
      if(result.includes('spotify')){
        playSpotifyLink=result;
        globalgenreForRecSp=''
      }
      else{
        playYoutubeLink=result
        globalgenreForRecYt=''
      }
      // loadRecents()
      //update the play variable link as per the api response
    })
    .catch((error) => {
      console.error("API call failed:", error);
      // document.getElementById("titleOfPage").value = bookName
      alert("Oops! Something went wrong while fetching book data.");
    });
}


//you might like section

function genreCardClick(genre, platform) {
  playlistByGenreSelect(genre,platform)
    .then((result) => {
      if (platform === 'youtube') {
        playYoutubeLink = result.playlistUrl;
        globalgenreForRecYt=genre;
        alert(`YouTube Playlist for ${genre} is ready! Click Play to listen.`);
      } else if (platform === 'spotify') {
        playSpotifyLink = result.playlistUrl;
        globalgenreForRecSp=genre;
        alert(`Spotify Playlist for ${genre} is ready! Click Play to listen.`);
      }
    })
    .catch((error) => {
      console.error("API call failed:", error);
      alert("Could not fetch the playlist. Try again later.");
    });
  
}


function getFilterValues() {
  // Get checkbox values
  const instrumentalChecked = document.getElementById("filter1").checked;
  const lyricalChecked = document.getElementById("filter2").checked;

  // Get selected language
  const selectedLanguage = document.getElementById("language").value;
  console.log(instrumentalChecked,lyricalChecked)
  return {
    instrument: instrumentalChecked,
    lyrical: lyricalChecked,
    language: selectedLanguage,
  };
}

window.addEventListener('load', () => {
  const hiddenElements = document.querySelectorAll('.hidden');
  hiddenElements.forEach((el, index) => {
    setTimeout(() => el.classList.add('show'), index * 500);
  });

  loadRecents();
  loadFavorites();
});



async function logout(){
  alert('Logged out!')
  window.location.href = "/";
}
let recentsList = [];  // Declare it globally

//recents
async function loadRecents() {
  try {
    const response = await fetch('/recents'); // <-- backend endpoint
    if (!response.ok) throw new Error("Failed to load recents");

    recentsList = await response.json(); // expect an array of recent items
    console.log(recentsList)
    renderRecents(recentsList);

  } catch (error) {
    console.error("Error fetching recents:", error);
    // Optionally show fallback UI or a message
  }
}


function renderRecents(recentsList) {
  const container = document.getElementById("recentsList");
  container.innerHTML = ""; // Clear previous items

  for (const [bookTitle, playlists] of Object.entries(recentsList)) {
    const details = document.createElement("details");

    const summary = document.createElement("summary");
    const bookNameDiv = document.createElement("div");
    bookNameDiv.className = "bookname";
    bookNameDiv.textContent = bookTitle;

    const arrowSpan = document.createElement("span");
    arrowSpan.className = "arrow";

    summary.appendChild(bookNameDiv);
    summary.appendChild(arrowSpan);
    details.appendChild(summary);

    const playlistsDiv = document.createElement("div");
    playlistsDiv.className = "playlists";
    console.log(playlists)
    playlists.forEach((item, index) => {
      const playlistDiv = document.createElement("div");
      playlistDiv.className = "playlist";

      const playlistName = document.createElement("span");
      playlistName.textContent = `Playlist ${index + 1}`;

      const playBtn = document.createElement("button");
      playBtn.className = "playlist_play_btn";
      playBtn.textContent = "Play";

      const breakDiv = document.createElement("div");
      breakDiv.className = "break";
      console.log(item)
      // let playLink = item.link;
      if (item!=null && item.includes('youtube')) {
        playBtn.addEventListener("click", () => {
          playYoutubeLink = item;
          alert("Use the YouTube Playcard!");
        });
      } else if (item!=null && item.includes('spotify')) {
        playBtn.addEventListener("click", () => {
          playSpotifyLink = item;
          alert("Use the Spotify Playcard!");
        });
      }

      playlistDiv.appendChild(playlistName);
      playlistDiv.appendChild(playBtn);
      playlistsDiv.appendChild(playlistDiv);
      playlistsDiv.appendChild(breakDiv);
    });

    details.appendChild(playlistsDiv);
    container.appendChild(details);
  }
}


//favorites
async function loadFavorites() {
  try {
    const response = await fetch("/favourite"); // API endpoint for favorites
    if (!response.ok) throw new Error("Failed to fetch favorites");

    const booksData = await response.json();
    renderFavorites(booksData);

  } catch (error) {
    console.error("Error loading favorites:", error);
    // Optionally display fallback UI or message
  }
}

function renderFavorites(booksData){
  
const container=document.getElementById("favSongs");

for (const [favBookName,playlist] of Object.entries(booksData)){
  const details=document.createElement("details");

  const summary=document.createElement("summary");
  const bookNameDiv=document.createElement("div");
  bookNameDiv.className="bookname"
  bookNameDiv.textContent=favBookName;

  const arrowSpan=document.createElement("span");
  arrowSpan.className="arrow";

  summary.appendChild(bookNameDiv);
  summary.appendChild(arrowSpan);
  details.appendChild(summary);

  const playlistsDiv=document.createElement("div");
  playlistsDiv.className="playlists";

  playlist.forEach((item,index) => {
    console.log(item)
    const playlistDiv=document.createElement("div");
    playlistDiv.className="playlist";

    const playlistName=document.createElement("span");
    playlistName.textContent= `Playlist ${index + 1}`;

    const playBtn=document.createElement("button");
    playBtn.className="playlist_play_btn";
    playBtn.textContent="Play";

    const breakDiv= document.createElement("div");
    breakDiv.className="break";

    // let playLink = item.link;
    if (item!=null && item.includes("youtube")){
      playBtn.addEventListener("click",() => {
        playYoutubeLink = item;
        alert("Use the YouTube Playcard!");
      })
    }
    else if (item!=null && item.includes("spotify")){
      playBtn.addEventListener("click", ()=> {
        playSpotifyLink = item;
        alert("Use the Spotify Playcard!");
      })
    }

    playBtn.addEventListener("click", () =>{

    });
    playlistDiv.appendChild(playlistName);
    playlistDiv.appendChild(playBtn);
    playlistsDiv.appendChild(playlistDiv);
    playlistsDiv.appendChild(breakDiv);
  });

  details.appendChild(playlistsDiv);
  container.appendChild(details);
}

}

async function showProfile(event) {
  event.preventDefault();
  console.log("clicking")
  try {
    const response = await fetch('/profile');  // Flask route to send user data

    if (!response.ok) throw new Error("Failed to fetch user profile");

    const data = await response.json();  // Expecting { name: "...", email: "..." }
    console.log('profile:',data)
    // Find the clicked element (or directly use document.querySelector('.user_name'))
    const userDiv = document.querySelector('.user_name');

    // Clear old contents (optional, if you want to replace them)
    userDiv.innerHTML = "";

    // Create and insert updated elements
    const nameHeading = document.createElement("h2");
    nameHeading.textContent = data.name;

    const emailSub = document.createElement("h6");
    emailSub.textContent = data.email;

    userDiv.appendChild(nameHeading);
    userDiv.appendChild(emailSub);

  } catch (error) {
    console.error("Error showing profile:", error);
    alert("Unable to load profile.");
  }
}


//previous button


async function goBack(event,platform) {
  event.preventDefault()
  if (recentsList.length === 0) {
    alert("No previous songs to go back to.");
    return;
  }

  try {
    const filters=getFilterValues()
    dataToSend={...filters,'platform':platform}
    const response = await fetch('/previous', {
      method: 'POST',
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(dataToSend)
    });

    if (!response.ok) throw new Error("Failed to go back.");

    const last = await response.json(); // backend returns the new list
    // recentsList = updatedRecents; // update local copy
    // renderRecents(recentsList);   // re-render the UI

    // if (recentsList.length > 0) {
    //   const last = recentsList[recentsList.length - 1];
      if (last.platform === 'youtube') {
        playYoutubeLink = last.link;
      } else if (last.platform === 'spotify') {
        playSpotifyLink = last.link;
      }
    // }

  } catch (error) {
    console.error("Error on go back:", error);
    alert("Something went wrong while going back.");
  }
}


async function SaveFavourite(event,platform){
  event.preventDefault()
  try {
    genre=null;
    link=null;
    if((platform=='spotify') && (globalgenreForRecSp!='')){
      link=playSpotifyLink;
      genre=globalgenreForRecSp
    }
    else if(platform=='youtube' && globalgenreForRecYt!=''){
      link=playYoutubeLink;
      genre=globalgenreForRecYt
    }
    dataToSend={'platform':platform,'link':link,'genre':genre}
    console.log("the data for favv:",dataToSend)
    const response = await fetch('/addFavourite', {
      method: 'PUT',
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(dataToSend)
    });

    const last = await response.json(); // backend returns the new list
    if (last.message =='done'){
      alert("Playlist Saved")
    }
    loadFavorites()

  } catch (error) {
    alert("Something went wrong while Saving.");
  }

}
//add to recents

async function addToRecents(title, platform, link) {
  const newRecent = { title, platform, link };

  try {
    const response = await fetch('/api/user/recents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newRecent)
    });

    if (!response.ok) throw new Error("Failed to add to recents");

    // Optionally update local recents list & UI
    recentsList.push(newRecent);
    renderRecents(recentsList);

  } catch (error) {
    console.error("Error adding to recents:", error);
  }
}
