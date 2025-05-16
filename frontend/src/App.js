import React, {useRef, useEffect, useState} from "react";
import {motion, AnimatePresence} from "framer-motion";
import axios from "axios";
import Swal from "sweetalert2";
import mainStyles from "./main.scss";

const App = () => {
    const mainRef = useRef();

    const [step, setStep] = useState("username");
    const [username, setUsername] = useState("");
    const [code, setCode] = useState("");
    const [userIconUrl, setUserIconUrl] = useState("");

    async function preloadImage(url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.src = url;
            img.onload = () => resolve();
            img.onerror = (err) => reject(err);
        });
    }

    async function handleRequestCode(e) {
        e.preventDefault();
        setStep("loading")
        try {
            const requestBody = {username};
            const response = await axios.post("/api/requestcode", requestBody);
            console.log(response.data);
            const imageUrl = response.data.user_icon_url;
            if(imageUrl !== null && imageUrl !== "") {
                setUserIconUrl(imageUrl);
                await preloadImage(imageUrl);
            }
            setStep("password")
        } catch (error) {
            console.error(error);
            Swal.fire({
                icon: "error",
                title: "An Unknown error occurred.",
                text: error.message
            });
        }
    }

    async function handleCodeSubmit(e) {
        e.preventDefault();
        try {
            const requestBody = {username, code};
            const response = await axios.post("/api/login", requestBody);
            console.log(response.data);
            setTimeout(() => {
                window.location.href = "/oauth/authorize" + window.location.search;
            }, 1000);

        } catch (error) {
            console.error(error);
            Swal.fire({
                icon: "error",
                title: "An Unknown error occurred.",
                text: error.message
            });
        }
    }

    useEffect(() => {
        const setMinHeight = () => {
            if (!mainRef.current) return;
            mainRef.current.style.minHeight = `${window.innerHeight}px`;
        };
        setMinHeight();
        window.addEventListener("resize", setMinHeight);
        return () => {
            window.removeEventListener("resize", setMinHeight);
        };
    }, []);

    return (
        <main ref={mainRef}>
            <AnimatePresence mode="wait">
                {step === "username" && (
                    <motion.form
                        key="username"
                        onSubmit={handleRequestCode}
                        initial={{opacity: 0, x: -30}}
                        animate={{opacity: 1, x: 0}}
                        exit={{opacity: 0, x: 30}}
                        transition={{duration: 0.3}}
                    >
                        <h1>Sign in</h1>
                        <input
                            type="text"
                            name="username"
                            placeholder="VRChat Username"
                            aria-label="VRChat Username"
                            autoComplete="username"
                            value={username}
                            required
                            onChange={e => setUsername(e.target.value)}
                        />
                       {/* <fieldset>
                            <label htmlFor="remember">
                                <input type="checkbox" role="switch" id="remember" name="remember"/>
                                Remember me
                            </label>
                        </fieldset>*/}
                        <button type="submit">
                            Request code
                        </button>
                    </motion.form>
                )}
                {step === "loading" && (
                    <motion.div
                    key="loading"
                    initial={{opacity: 0}}
                    animate={{opacity: 1}}
                    exit={{opacity: 0}}
                    transition={{duration: 0.3}}
                    >
                        <h1>Loading...</h1>
                        <p>Please wait while we check your profile.</p>
                    </motion.div>
                )}
                {step === "password" && (
                    <motion.form
                        key="password"
                        onSubmit={handleCodeSubmit}
                        initial={{opacity: 0, x: 30}}
                        animate={{opacity: 1, x: 0}}
                        exit={{opacity: 0, x: -30}}
                        transition={{duration: 0.3}}
                    >
                        <h1>Logging in as {username}</h1>
                        <img
                            src={userIconUrl || ""}
                            alt="Profile picture"
                            style={{
                                borderRadius: "50%",
                                objectFit: "cover",
                                paddingBottom: "1rem",
                            }}
                        />
                        <input
                            type="code"
                            placeholder="Code"
                            value={code}
                            onChange={(e) => setCode(e.target.value)}
                            required
                        />
                        <button type="button" onClick={() => setStep("username")}>
                            ← Back
                        </button>
                        <button type="submit">
                            Login
                        </button>
                    </motion.form>
                )}
            </AnimatePresence>
        </main>
    )
        ;
};
export default App;
