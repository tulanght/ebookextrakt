import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  const [apiStatus, setApiStatus] = useState<string>('Đang kiểm tra kết nối API...')

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/ping')
      .then(res => res.json())
      .then(data => {
        setApiStatus(`Kết nối API thành công: ${JSON.stringify(data)}`)
      })
      .catch(err => {
        setApiStatus(`Lỗi kết nối API: ${err.message}`)
      })
  }, [])

  return (
    <>
      <section id="center">
        <div className="hero">
          <img src={heroImg} className="base" width="170" height="179" alt="" />
          <img src={reactLogo} className="framework" alt="React logo" />
          <img src={viteLogo} className="vite" alt="Vite logo" />
        </div>
        <div>
          <h1>ExtractPDF-EPUB (Electron)</h1>
          <p>
            Edit <code>src/App.tsx</code> and save to test <code>HMR</code>
          </p>
          <div style={{ marginTop: '20px', padding: '10px', background: '#333', borderRadius: '8px' }}>
            <strong>Backend Status: </strong> 
            <span style={{ color: apiStatus.includes('thành công') ? '#4ade80' : '#f87171' }}>
              {apiStatus}
            </span>
          </div>
        </div>
        <button
          type="button"
          className="counter"
          onClick={() => setCount((count) => count + 1)}
          style={{ marginTop: '20px' }}
        >
          Count is {count}
        </button>
      </section>

      <div className="ticks"></div>
    </>
  )
}

export default App
