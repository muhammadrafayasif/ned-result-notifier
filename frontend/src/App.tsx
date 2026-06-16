import { useEffect, useRef, useState } from "react";
import { Route, Routes, useNavigate, useSearchParams } from "react-router-dom";
import "./App.css";
import {
  Activity,
  Atom,
  Beaker,
  BookMarked,
  BookOpen,
  Box,
  Brain,
  Briefcase,
  Building2,
  Car,
  Code,
  Cpu,
  Database,
  DollarSign,
  Droplets,
  Factory,
  Gamepad2,
  Hammer,
  HardHat,
  Layers,
  Lock,
  Radio,
  TrendingUp,
  UtensilsCrossed,
  Wrench,
  Wifi,
  Wind,
  Zap,
} from "lucide-react";

const DEPARTMENTS = [
  { value: "0", name: "Architecture", icon: Building2 },
  { value: "1", name: "Physics", icon: Atom },
  { value: "2", name: "Artificial Intelligence", icon: Brain },
  { value: "3", name: "Computational Finance", icon: TrendingUp },
  { value: "4", name: "Computer Science", icon: Code },
  { value: "5", name: "Computer Science (TIEST)", icon: Code },
  { value: "6", name: "Cyber Security", icon: Lock },
  { value: "7", name: "Data Science", icon: Database },
  { value: "8", name: "Development Studies", icon: BookOpen },
  { value: "9", name: "Economics & Finance", icon: DollarSign },
  { value: "10", name: "English Linguistics", icon: BookMarked },
  { value: "11", name: "Gaming and Animation", icon: Gamepad2 },
  { value: "12", name: "Chemistry", icon: Beaker },
  { value: "13", name: "Management Sciences", icon: Briefcase },
  { value: "14", name: "Textile Sciences", icon: Layers },
  { value: "15", name: "Automotive Engg.", icon: Car },
  { value: "16", name: "Bio-Medical Engg.", icon: Activity },
  { value: "17", name: "Chemical Engg.", icon: Droplets },
  { value: "18", name: "Civil Engg.", icon: HardHat },
  { value: "19", name: "Civil Engg. (TIEST)", icon: HardHat },
  { value: "20", name: "Computer Systems Engg.", icon: Cpu },
  { value: "21", name: "Construction Engg.", icon: Hammer },
  { value: "22", name: "Electrical Engg.", icon: Zap },
  { value: "23", name: "Electronics Engg.", icon: Wifi },
  { value: "24", name: "Food Engg.", icon: UtensilsCrossed },
  { value: "25", name: "Industrial & Manufacturing Engg.", icon: Factory },
  { value: "26", name: "Materials Engg.", icon: Box },
  { value: "27", name: "Mechanical Engg.", icon: Wrench },
  { value: "28", name: "Metallurgical Engg.", icon: Layers },
  { value: "29", name: "Petroleum Engg.", icon: Droplets },
  { value: "30", name: "Polymer & Petrochemical Engg.", icon: Droplets },
  { value: "31", name: "Software Engg.", icon: Code },
  { value: "32", name: "Telecommunications Engg.", icon: Radio },
  { value: "33", name: "Textile Engg.", icon: Wind },
  { value: "34", name: "Urban Engg.", icon: Building2 },
];

const APP_KEY = import.meta.env.VITE_APP_KEY ?? "";
const BASE_API = import.meta.env.VITE_BASE_API;

const authHeaders = {
  "X-App-Key": APP_KEY,
};

const apiUrl = (path: string) => `${BASE_API.replace(/\/$/, "")}${path}`;

type FormDataState = {
  email: string;
  department: string;
  year: string;
};

export default function App() {
  return (
    <Routes>
      <Route path="/user" element={<DeleteUserPage />} />
      <Route path="*" element={<HomePage />} />
    </Routes>
  );
}

function HomePage() {
  const [allResultsReleased, setResultsReleased] = useState(false);
  const [denySubmission, setSubmissionDisabled] = useState(true);
  const [examName, setExam] = useState("");
  const [formData, setFormData] = useState<FormDataState>({
    email: "",
    department: "",
    year: "",
  });
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("");
  const carouselRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(apiUrl("/get_details"), { headers: authHeaders })
      .then((res) => res.json())
      .then((data) => {
        setResultsReleased(data.all_results_released);
        setExam(data.exam_name);
        if (!data.all_results_released) setSubmissionDisabled(false);
      })
      .catch((err) => console.error("Error fetching details:", err));
  }, []);

  const clearSubmissionLock = () => {
    if (status === "error") {
      setSubmissionDisabled(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    if (e.target.value === "UUDDLRLRBAS") setSubmissionDisabled(false);
    else clearSubmissionLock();
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const selectDepartment = (value: string) => {
    clearSubmissionLock();
    setFormData({
      ...formData,
      department: value,
      year: "1",
    });
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!carouselRef.current) return;

    const startX = e.clientX;
    const startScrollLeft = carouselRef.current.scrollLeft;
    const isDragging = { current: false };

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const distance = Math.abs(moveEvent.clientX - startX);
      if (!isDragging.current && distance > 5) {
        isDragging.current = true;
      }

      if (isDragging.current && carouselRef.current) {
        carouselRef.current.scrollLeft = startScrollLeft - (moveEvent.clientX - startX);
      }
    };

    const handleMouseUp = () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  };

  const scroll = (direction: "left" | "right") => {
    if (!carouselRef.current) return;

    carouselRef.current.scrollBy({
      left: direction === "left" ? -300 : 300,
      behavior: "smooth",
    });
  };

  const handleForm = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setStatus("loading");
    setSubmissionDisabled(true);
    setMessage("");

    try {
      const response = await fetch(apiUrl("/insert_user"), {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ ...formData, examName }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Submission failed");
      }

      setFormData({ email: "", department: "", year: "" });
      setStatus("success");
      setMessage("You will be notified when results are released.");
      setSubmissionDisabled(false);
    } catch (error: any) {
      setStatus("error");
      setMessage(error.message || "Something went wrong. Please try again.");
    }
  };

  return (
    <div className="results-container">
      <div
        className="github-banner"
        onClick={() => window.open("https://www.github.com/muhammadrafayasif/ned-result-notifier", "_blank")}
      >
        <img src="/github.webp" alt="GitHub Logo" />
        Star on GitHub
      </div>

      <form className="results-form" onSubmit={handleForm}>
        {examName && <div className="status-message success exam-name">{examName}</div>}

        {allResultsReleased && (
          <div className="status-message loading">
            All results have now been officially released, you may view them from the <a href="https://www.neduet.edu.pk/examination_results">NEDUET website</a>.
          </div>
        )}

        <div className="form-header">
          <h1>NEDUET Results Notifier</h1>
        </div>

        <div className="form-section">
          <label className="section-label">Cloud Email Address</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            placeholder="you@cloud.neduet.edu.pk"
            className="form-input"
          />
        </div>

        <div className="form-section">
          <label className="section-label">Select Department</label>
          <div className="carousel-wrapper">
            <button type="button" className="carousel-btn carousel-btn-left" onClick={() => scroll("left")} aria-label="Scroll left">
              ‹
            </button>
            <div className="carousel-container" onMouseDown={handleMouseDown}>
              <div className="carousel-items" ref={carouselRef}>
                {DEPARTMENTS.map((dept) => {
                  const IconComponent = dept.icon;
                  return (
                    <div
                      key={dept.value}
                      className={`dept-card ${formData.department === dept.value ? "selected" : ""}`}
                      onClick={() => selectDepartment(dept.value)}
                    >
                      <IconComponent size={32} strokeWidth={1.5} />
                      <div className="dept-name">{dept.name}</div>
                    </div>
                  );
                })}
              </div>
            </div>
            <button type="button" className="carousel-btn carousel-btn-right" onClick={() => scroll("right")} aria-label="Scroll right">
              ›
            </button>
          </div>
        </div>

        <div className="form-section">
          <label className="section-label">Year</label>
          <div className="year-buttons">
            {[1, 2, 3, 4].map((year) => (
              <button
                key={year}
                type="button"
                className={`year-btn ${formData.year === year.toString() ? "active" : ""}`}
                onClick={() => {
                  clearSubmissionLock();
                  setFormData({
                    ...formData,
                    year: year.toString(),
                  });
                }}
              >
                Year {year}
              </button>
            ))}
            {formData.department === "0" && (
              <button
                type="button"
                className={`year-btn ${formData.year === "5" ? "active" : ""}`}
                onClick={() => {
                  clearSubmissionLock();
                  setFormData({
                    ...formData,
                    year: "5",
                  });
                }}
              >
                Year 5
              </button>
            )}
          </div>
        </div>

        <button
          type="submit"
          disabled={denySubmission || !formData.email || !formData.department || !formData.year}
          className="submit-btn"
        >
          {status === "loading" ? <span className="loading-spinner">⟳</span> : "Notify Me"}
        </button>

        {message && <div className={`status-message ${status}`}>{message}</div>}
      </form>
    </div>
  );
}

function DeleteUserPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [deleteStatus, setDeleteStatus] = useState<"loading" | "success" | "error">("loading");
  const [deleteMessage, setDeleteMessage] = useState("Removing your details...");
  const deleteRequestSentRef = useRef(false);

  useEffect(() => {
    if (deleteRequestSentRef.current) return;
    deleteRequestSentRef.current = true;

    const id = searchParams.get("id");
    if (!id) {
      setDeleteStatus("error");
      setDeleteMessage("Missing deletion id.");
      return;
    }

    fetch(apiUrl(`/remove_user?id=${encodeURIComponent(id)}`), {
      headers: authHeaders,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("We could not delete your entry.");
        }

        setDeleteStatus("success");
        setDeleteMessage("Your email has been removed from the notification list.");
      })
      .catch((error: any) => {
        setDeleteStatus("error");
        setDeleteMessage(error.message || "Something went wrong while removing your entry.");
      });
  }, [searchParams]);

  return (
    <div className="results-container">
      <div className="results-form delete-page">
        <div className={`delete-icon ${deleteStatus}`}>
          {deleteStatus === "success" ? "✓" : deleteStatus === "error" ? "!" : "…"}
        </div>
        <h1 className="delete-title">
          {deleteStatus === "success" ? "User Deleted" : deleteStatus === "error" ? "Deletion Failed" : "Removing User"}
        </h1>
        <p className="delete-message">{deleteMessage}</p>
        <button type="button" className="submit-btn" onClick={() => navigate("/")}>Back to Home</button>
      </div>
    </div>
  );
}
