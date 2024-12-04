import React, { useEffect, useRef, useState } from 'react';
import Quill from 'quill';
import 'quill/dist/quill.snow.css';

const CursorTracker = () => {
  const editorRef = useRef(null);
  const quillRef = useRef(null);
  const wsRef = useRef(null);
  
  useEffect(() => {
    const docId = window.location.pathname.split('/').filter(Boolean).pop();
    const cursorModule = {
      cursors: {},
      createCursor(username, color) {
        const cursor = document.createElement('span');
        cursor.className = 'custom-cursor';
        cursor.style.backgroundColor = color;
        cursor.innerHTML = `<span class="cursor-flag" style="background-color: ${color}">${username}</span>`;
        return cursor;
      },
      moveCursor(username, position) {
        const cursor = this.cursors[username];
        if (cursor && position) {
          const [index, length] = position;
          const bounds = quillRef.current.getBounds(index, length);
          cursor.style.left = `${bounds.left}px`;
          cursor.style.top = `${bounds.top}px`;
          cursor.style.height = `${bounds.height}px`;
        }
      },
      trackCursor(username, position) {
        if (!this.cursors[username]) {
          const color = `hsl(${Math.random() * 360}, 70%, 50%)`;
          this.cursors[username] = this.createCursor(username, color);
          editorRef.current.querySelector('.ql-editor').appendChild(this.cursors[username]);
        }
        this.moveCursor(username, position);
      }
    };

    // Initialize Quill
    quillRef.current = new Quill(editorRef.current, {
      theme: 'snow',
      modules: {
        toolbar: [
          [{ 'header': [1, 2, 3, false] }],
          ['bold', 'italic', 'underline', 'strike'],
          [{ 'list': 'ordered'}, { 'list': 'bullet' }],
          [{ 'color': [] }, { 'background': [] }],
          ['clean']
        ]
      }
    });

    // Set initial content if available
    const initialContent = document.getElementById('initial-content');
    if (initialContent) {
      const content = JSON.parse(initialContent.textContent);
      quillRef.current.setContents(content);
    }

    // WebSocket setup
    wsRef.current = new WebSocket(`ws://${window.location.host}/ws/editor/${docId}/`);
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'cursor') {
        cursorModule.trackCursor(data.username, data.position);
      } else if (data.type === 'content') {
        const currentIndex = quillRef.current.getSelection()?.index;
        quillRef.current.updateContents(data.content);
        if (currentIndex !== undefined) {
          quillRef.current.setSelection(currentIndex);
        }
      }
    };

    // Track local cursor position
    quillRef.current.on('selection-change', (range) => {
      if (range && wsRef.current) {
        wsRef.current.send(JSON.stringify({
          type: 'cursor',
          position: [range.index, range.length]
        }));
      }
    });

    // Handle text changes
    quillRef.current.on('text-change', (delta) => {
      if (wsRef.current) {
        wsRef.current.send(JSON.stringify({
          type: 'content',
          content: { ops: delta.ops }
        }));
      }
    });

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return (
    <div className="h-full w-full">
      <style>
        {`
          .custom-cursor {
            position: absolute;
            width: 2px;
            pointer-events: none;
            transition: all 0.1s ease;
          }
          .cursor-flag {
            position: absolute;
            top: -18px;
            left: 0;
            color: white;
            padding: 2px 4px;
            font-size: 12px;
            white-space: nowrap;
            border-radius: 3px;
          }
        `}
      </style>
      <div ref={editorRef} className="h-full" />
    </div>
  );
};

export default CursorTracker;