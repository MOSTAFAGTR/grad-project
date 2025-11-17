import React from "react";

const XssTutorialPage: React.FC = () => {
  return (
    <div className="text-white">
      <h1 className="text-4xl font-bold mb-2">XSS Tutorial</h1>
      <p className="text-gray-400 mb-8">
        This page explains how Cross-Site Scripting (XSS) attacks work and how
        to prevent them. The fix for this challenge will escape user-supplied
        content before rendering in the page.
      </p>

      <ul className="list-disc ml-6">
        <li>
          Reflected vs Stored XSS: This challenge demonstrates stored XSS — user
          input is stored and shown to any user visiting the message page.
        </li>
        <li>
          Fix: Sanitize and escape any user-provided values. Use safe
          templating, or markupsafe.escape to protect content.
        </li>
        <li>
          Additional: Validate and sanitize inputs, implement Content Security
          Policy (CSP), and avoid inserting HTML directly.
        </li>
      </ul>
    </div>
  );
};

export default XssTutorialPage;
