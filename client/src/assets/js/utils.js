const API_URL = 'http://sxbn.org:8080' ;


export async function login(username, password) {
    let errorMessage = null;
    let token = null;
    console.log("login in with ", username, password);
    const data = new URLSearchParams();
    data.append("username", username);
    data.append("password", password);
    const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: data,
    };
    try {
        const response = await fetch(API_URL+'/token', requestOptions);
        const data = await response.json();
        if (!response.ok) {
            const error = (data && data.message) || response.status;
            return Promise.reject(error);
        }
        console.log("user creation successful", data)
        if (data.access_token) {
            token = data.access_token
        } else {
            console.log("login failed", data.detail);
            errorMessage = "login failed";
        }
    } catch (error) {
        console.error('There was an error!', error);
        errorMessage = "login failed";
    }
    return {token, errorMessage};
}



export async function register(username, email, password) {
    let errorMessage = null;
    let token = null;
    console.log("user creation with ", username, email, password);
    const data = {
        username: username,
        email: email,
        plain_password: password,
        full_name: '',
    };

    const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    };
    try {
        const response = await fetch(API_URL+'/users', requestOptions);
        const data = await response.json();
        if (response.status == 409) {
            errorMessage = data.detail;
        }else if (!response.ok) {
            const error = (data && data.message) || response.status;
            return Promise.reject(error);
        }
        // logs in automatically
        const result = await login(username, password);
        token = result.token;
        errorMessage = result.errorMessage;
    } catch(error) {
                console.error('There was an error!', error);
                errorMessage = "user creation failed";
    }
    return {token, errorMessage};
}

export async function getUserInfo(token) {
    let username = null;
    let error = null;
    const requestOptions = {
        method: 'GET',
        headers: { 
            'accept': 'application/json',
            'Authorization': 'Bearer '+token,
        }
    }
    try {
        const response = await fetch(API_URL+'/users/me', requestOptions);
        const data = await response.json();
        if (!response.ok) {
            error = (data && data.message) || response.status;
        } else {
            username = data.username;
        }
    } catch(err) {
        console.error('There was an error!', err);
        error = String(err);
    }
    return {username, error};

}