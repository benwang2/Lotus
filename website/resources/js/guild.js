let json = "";

{
    function process_leaderboard(){
        template = document.querySelector("#card-template")
        guild_id = ""+(window.location)
        wrapper = document.querySelector(".wrapper")

        guild_id = guild_id.replace(/(http|https)?(.*)(guilds\/)/g, '')
        generated_at = 0

        fetch("/json/"+guild_id)
            .then (res => res.json())
            .then (data => {
                generated_at = data['generated']

                json = data // for debugging purposes

                date = new Date(0);
                date.setUTCSeconds(generated_at)
                time = date.toLocaleString('en-us',{timeZoneName:'short'})

                time = time.replace(/([\d]*[/,]){3} /g,"")
                document.querySelector("#footer").innerHTML = "Generated at "+time

                for (let i = 0; i < data['members'].length; i++){
                    member = data['members'][i]

                    clone = template.cloneNode(true)
                    clone.id = "member"+(i+1);

                    rank = clone.querySelector(".rank")
                    rank.innerHTML = i+1

                    clone.querySelector(".username").innerHTML = member['username']
                    clone.querySelector(".pfp").style = "background-image: url('"+member["pfp"]+"')"
                    
                    stats = clone.querySelectorAll(".stat-display")

                    stats[0].childNodes[3].innerHTML = member['messages']
                    stats[1].childNodes[3].innerHTML = member['voice']
                    stats[2].childNodes[3].innerHTML = member['points']

                    clone.classList.toggle("hidden", false)

                    if (i < 3){
                        rank.classList.toggle("one",true)
                    } else if (i < 8) {
                        rank.classList.toggle("two",true)
                    } else if (i < 15) {
                        rank.classList.toggle("three",true)
                    } else {
                        rank.classList.toggle("four",true)
                    }

                    wrapper.appendChild(clone)
                }
            }
        )
    }

    on_loaded_calls.push(process_leaderboard)

}


