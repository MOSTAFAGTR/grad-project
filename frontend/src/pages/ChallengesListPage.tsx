import React from "react";
import { Link } from "react-router-dom";
import {
  FaSyringe,
  FaBug,
  FaUserSecret,
  FaTerminal,
  FaUserShield,
  FaTools,
  FaLock,
  FaFolderOpen,
  FaFileCode,
  FaExternalLinkAlt,
} from "react-icons/fa";

// This map is used for the border, text, and shadow colors
const colorMap: Record<string, string> = {
  cyan: "#06b6d4",
  pink: "#d946ef",
  orange: "#fb923c",
  purple: "#8b5cf6",
  red: "#ef4444",
  green: "#10b981",
  yellow: "#facc15",
  blue: "#3b82f6",
  indigo: "#6366f1",
  teal: "#14b8a6",
};

const challenges = [
  {
    id: 1,
    title: "SQL Scenario",
    icon: <FaSyringe />,
    color: "cyan",
    buttons: [
      { text: "Simulate", url: "/challenges/1/attack" },
      { text: "Fix", url: "/challenges/1/fix" },
      { text: "Tutorial", url: "/challenges/1/tutorial" },
    ],
  },
  {
    id: 2,
    title: "XSS Scenario",
    icon: <FaBug />,
    color: "pink",
    buttons: [
      { text: "Simulate", url: "/challenges/2/attack" },
      { text: "Fix", url: "/challenges/2/fix" },
      { text: "Tutorial", url: "/challenges/2/tutorial" },
    ],
  },
  {
    id: 3,
    title: "CSRF Scenario",
    icon: <FaUserSecret />,
    color: "orange",
    buttons: [
      { text: "Simulate", url: "/under-construction" },
      { text: "Fix", url: "/under-construction" },
      { text: "Tutorial", url: "/under-construction" },
    ],
  },
  {
    id: 4,
    title: "Command Injection",
    icon: <FaTerminal />,
    color: "purple",
    buttons: [
      { text: "Simulate", url: "/under-construction" },
      { text: "Fix", url: "/under-construction" },
      { text: "Tutorial", url: "/under-construction" },
    ],
  },
  {
    id: 5,
    title: "Broken Authentication",
    icon: <FaUserShield />,
    color: "red",
    buttons: [
      { text: "Simulate", url: "/under-construction" },
      { text: "Fix", url: "/under-construction" },
      { text: "Tutorial", url: "/under-construction" },
    ],
  },
  {
    id: 6,
    title: "Security Misconfiguration",
    icon: <FaTools />,
    color: "green",
    buttons: [
      { text: "Simulate", url: "/under-construction" },
      { text: "Fix", url: "/under-construction" },
      { text: "Tutorial", url: "/under-construction" },
    ],
  },
  {
    id: 7,
    title: "Insecure Storage",
    icon: <FaLock />,
    color: "yellow",
    buttons: [
      { text: "Simulate", url: "/under-construction" },
      { text: "Fix", url: "/under-construction" },
      { text: "Tutorial", url: "/under-construction" },
    ],
  },
  {
    id: 8,
    title: "Directory Traversal",
    icon: <FaFolderOpen />,
    color: "blue",
    buttons: [
      { text: "Simulate", url: "/under-construction" },
      { text: "Fix", url: "/under-construction" },
      { text: "Tutorial", url: "/under-construction" },
    ],
  },
  {
    id: 9,
    title: "XML External Entity (XXE)",
    icon: <FaFileCode />,
    color: "indigo",
    buttons: [
      { text: "Simulate", url: "/under-construction" },
      { text: "Fix", url: "/under-construction" },
      { text: "Tutorial", url: "/under-construction" },
    ],
  },
  {
    id: 10,
    title: "Unvalidated Redirect",
    icon: <FaExternalLinkAlt />,
    color: "teal",
    buttons: [
      { text: "Simulate", url: "/under-construction" },
      { text: "Fix", url: "/under-construction" },
      { text: "Tutorial", url: "/under-construction" },
    ],
  },
  {
     id: 2,
     title: 'XSS Scenario',
     icon: <FaBug />,
     color: 'pink',
     buttons: [
     { text: 'Simulate', url: '/challenges/2/attack' },
      { text: 'Fix', url: '/challenges/2/fix' },
      { text: 'Tutorial', url: '/challenges/2/tutorial' }
    ] 
    },
  { id: 3, title: 'CSRF Scenario', icon: <FaUserSecret />, color: 'orange', buttons: [{ text: 'Simulate', url: '/under-construction' }, { text: 'Fix', url: '/under-construction' }, { text: 'Tutorial', url: '/under-construction' }] },
  { id: 4, title: 'Command Injection', icon: <FaTerminal />, color: 'purple', buttons: [{ text: 'Simulate', url: '/under-construction' }, { text: 'Fix', url: '/under-construction' }, { text: 'Tutorial', url: '/under-construction' }] },
  { id: 5, title: 'Broken Authentication', icon: <FaUserShield />, color: 'red', buttons: [{ text: 'Simulate', url: '/under-construction' }, { text: 'Fix', url: '/under-construction' }, { text: 'Tutorial', url: '/under-construction' }] },
  { id: 6, title: 'Security Misconfiguration', icon: <FaTools />, color: 'green', buttons: [{ text: 'Simulate', url: '/under-construction' }, { text: 'Fix', url: '/under-construction' }, { text: 'Tutorial', url: '/under-construction' }] },
  { id: 7, title: 'Insecure Storage', icon: <FaLock />, color: 'yellow', buttons: [{ text: 'Simulate', url: '/under-construction' }, { text: 'Fix', url: '/under-construction' }, { text: 'Tutorial', url: '/under-construction' }] },
  { id: 8, title: 'Directory Traversal', icon: <FaFolderOpen />, color: 'blue', buttons: [{ text: 'Simulate', url: '/under-construction' }, { text: 'Fix', url: '/under-construction' }, { text: 'Tutorial', url: '/under-construction' }] },
  { id: 9, title: 'XML External Entity (XXE)', icon: <FaFileCode />, color: 'indigo', buttons: [{ text: 'Simulate', url: '/under-construction' }, { text: 'Fix', url: '/under-construction' }, { text: 'Tutorial', url: '/under-construction' }] },
  { id: 10, title: 'Unvalidated Redirect', icon: <FaExternalLinkAlt />, color: 'teal', buttons: [{ text: 'Simulate', url: '/under-construction' }, { text: 'Fix', url: '/under-construction' }, { text: 'Tutorial', url: '/under-construction' }] }
];

const ChallengesListPage: React.FC = () => {
  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-8">
        {challenges.map((ch) => (
          <div
            key={ch.id}
            className="card-container bg-gray-900 rounded-2xl p-6 flex flex-col border-2 transition-all duration-300"
            style={
              {
                borderColor: colorMap[ch.color],
                "--shadow-color": colorMap[ch.color],
              } as React.CSSProperties
            }
          >
            <div className="flex-grow">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-white text-2xl font-bold">{ch.title}</h3>
                <div
                  className="text-5xl icon-container"
                  style={{ color: colorMap[ch.color] }}
                >
                  {ch.icon}
                </div>
              </div>
            </div>
            <div className="flex flex-wrap gap-3 mt-8">
              {ch.buttons.map((btn) => (
                <Link
                  key={btn.text}
                  to={btn.url}
                  className="bg-gray-700 text-gray-300 text-sm font-semibold py-2 px-5 rounded-full hover:bg-gray-600 hover:text-white transition-colors"
                >
                  {btn.text}
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
      <style>
        {`
          .card-container:hover {
            transform: translateY(--5px) scale(1.02);
            box-shadow: 0 10px 20px -5px var(--shadow-color);
          }
          .icon-container {
            transition: transform 0.3s ease-in-out;
          }
          .card-container:hover .icon-container {
            transform: scale(1.2) rotate(5deg);
          }
        `}
      </style>
    </>
  );
};

export default ChallengesListPage;
