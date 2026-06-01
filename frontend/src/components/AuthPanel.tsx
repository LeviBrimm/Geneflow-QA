import { LogIn, UserPlus } from "lucide-react";
import { FormEvent, useState } from "react";

import { login, register, tokenStore } from "../lib/api";

export function AuthPanel({ onAuthed }: { onAuthed: () => void }) {
  const [mode, setMode] = useState<"register" | "login">("register");
  const [email, setEmail] = useState("qa@example.com");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const response = mode === "register" ? await register(email, password) : await login(email, password);
      tokenStore.set(response.access_token);
      onAuthed();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed.");
    }
  }

  return (
    <form className="auth-form" onSubmit={submit}>
      <div className="segmented">
        <button type="button" className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>
          <UserPlus size={16} />
          <span>Register</span>
        </button>
        <button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>
          <LogIn size={16} />
          <span>Login</span>
        </button>
      </div>
      <label>
        Email
        <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
      </label>
      <label>
        Password
        <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" minLength={8} required />
      </label>
      <button className="primary-button" type="submit">
        {mode === "register" ? <UserPlus size={18} /> : <LogIn size={18} />}
        <span>{mode === "register" ? "Create Account" : "Log In"}</span>
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
