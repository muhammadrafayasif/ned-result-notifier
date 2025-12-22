import { useState } from "react";
import "./App.css";

const ResultsNotification = () => {
  const [formData, setFormData] = useState({
    email: "",
    department: "",
    year: ""
  });

  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleForm = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setStatus("loading");
    setMessage("");

    try {
      const response = await fetch("https://ned-result-notifier.vercel.app/add", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Submission failed");
      }

      setFormData({
        email: "",
        department: "",
        year: ""
      });

      setStatus("success");
      setMessage("You will be notified when results are released.");
    } catch (error: any) {
      setStatus("error");
      setMessage(error.message || "Something went wrong. Please try again.");
    }
  };

  return (
    <div className="results-container">
      <form className="results-form" onSubmit={handleForm}>
        <h2>NEDUET Results Notification</h2>
        <p>Enter your details to get emailed when results are released.</p>

        <label>Email Address</label>
        <input
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          required
          placeholder="you@example.com"
        />

        <label>Department</label>
        <select
          name="department"
          value={formData.department}
          onChange={handleChange}
          required
        >
          <option value="">Select Department</option>
          <option value="0">Architecture</option>
          <option value="1">Physics</option>
          <option value="2">Artificial Intelligence</option>
          <option value="3">Computational Finance</option>
          <option value="4">Computer Science</option>
          <option value="5">Computer Science (TIEST)</option>
          <option value="6">Cyber Security</option>
          <option value="7">Data Science</option>
          <option value="8">Development Studies</option>
          <option value="9">Economics & Finance</option>
          <option value="10">English Linguistics</option>
          <option value="11">Gaming and Animation</option>
          <option value="12">Chemistry</option>
          <option value="13">Management Sciences</option>
          <option value="14">Textile Sciences</option>
          <option value="15">Automotive Engg.</option>
          <option value="16">Bio-Medical Engg.</option>
          <option value="17">Chemical Engg.</option>
          <option value="18">Civil Engg.</option>
          <option value="19">Civil Engg. (TIEST)</option>
          <option value="20">Computer Systems Engg.</option>
          <option value="21">Construction Engg.</option>
          <option value="22">Electrical Engg.</option>
          <option value="23">Electronics Engg.</option>
          <option value="24">Food Engg.</option>
          <option value="25">Industrial & Manufacturing Engg.</option>
          <option value="26">Materials Engg.</option>
          <option value="27">Mechanical Engg.</option>
          <option value="28">Metallurgical Engg.</option>
          <option value="29">Petroleum Engg.</option>
          <option value="30">Polymer & Petrochemical Engg.</option>
          <option value="31">Software Engg.</option>
          <option value="32">Telecommunications Engg.</option>
          <option value="33">Textile Engg.</option>
          <option value="34">Urban Engg.</option>
        </select>

        <label>Year</label>
        <select
          name="year"
          value={formData.year}
          onChange={handleChange}
          required
        >
          <option value="">Select Year</option>
          <option value="1">1st Year</option>
          <option value="2">2nd Year</option>
          <option value="3">3rd Year</option>
          <option value="4">4th Year</option>
          {formData.department == "0" && <option value="5">5th Year</option>}
        </select>

        <button type="submit" disabled={status === "loading"}>
          {status === "loading" ? "Submitting..." : "Notify Me"}
        </button>

        {message && (
          <div className={`status-message ${status}`}>
            {message}
          </div>
        )}
      </form>
    </div>
  );
};

export default ResultsNotification;
