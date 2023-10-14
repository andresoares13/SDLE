document.getElementById("loginButton").addEventListener("click", function() {
    var username = document.getElementById("loginUsername").value;
    var password = document.getElementById("loginPassword").value;
    
    // Create an object to hold the data
    var data = {
        name: username,
        password: password
    };

    // Send the data to the server using the Fetch API
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (response.status === 200) {
            console.log("Connected to server");
        } else {
            console.log("Login failed");
        }
    });
});
