"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  CheckCircle,
  Clock,
  TrendingUp,
  AlertCircle,
  BarChart3,
  Calculator,
  Users,
  Target,
  MessageCircle,
  HelpCircle,
} from "lucide-react"
import { JSX } from "react/jsx-runtime"

interface InterviewState {
  sessionId: string | null
  candidateName: string
  positionLevel: string
  currentMessage: string
  currentQuestion: string | null
  currentQuestionFormat: string
  currentOptions: string[] | null
  isComplete: boolean
  assessmentResult: any | null
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

// Function to render tables in questions
const renderQuestionWithTables = (question: string) => {
  // Split question into lines to process tables properly
  const lines = question.split('\n')
  const result: JSX.Element[] = []
  let currentTextLines: string[] = []
  let i = 0

  const flushTextLines = () => {
    if (currentTextLines.length > 0) {
      const text = currentTextLines.join('\n').trim()
      if (text) {
        result.push(
          <p key={`text-${result.length}`} className="mb-4 text-gray-800 leading-relaxed whitespace-pre-wrap">
            {text}
          </p>
        )
      }
      currentTextLines = []
    }
  }

  while (i < lines.length) {
    const line = lines[i]

    // Check if this line looks like a table header (contains multiple |)
    if (line.includes('|') && line.split('|').length >= 3) {
      // Look ahead to see if next line is a separator (contains ---)
      const nextLine = i + 1 < lines.length ? lines[i + 1] : ''

      if (nextLine.includes('---') && nextLine.includes('|')) {
        // We found a table! Flush any accumulated text first
        flushTextLines()

        // Parse the table
        const headerLine = line
        const dataLines: string[] = []

        // Collect data rows
        let j = i + 2
        while (j < lines.length && lines[j].includes('|') && lines[j].split('|').length >= 3) {
          dataLines.push(lines[j])
          j++
        }

        // Parse headers
        const headers = headerLine
          .split('|')
          .map(h => h.trim())
          .filter(h => h !== '')

        // Parse data rows
        const rows = dataLines.map(line =>
          line
            .split('|')
            .map(cell => cell.trim())
            .filter(cell => cell !== '')
        )

        // Only render table if we have valid data
        if (headers.length > 0 && rows.length > 0) {
          result.push(
            <div key={`table-${result.length}`} className="my-6 overflow-x-auto">
              <table className="min-w-full border-collapse border border-gray-300 bg-white shadow-sm rounded-lg">
                <thead>
                  <tr className="bg-green-600 text-white">
                    {headers.map((header, headerIndex) => (
                      <th key={headerIndex} className="border border-gray-300 px-4 py-3 text-left font-semibold">
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, rowIndex) => (
                    <tr key={rowIndex} className={rowIndex % 2 === 0 ? "bg-white" : "bg-green-50"}>
                      {row.map((cell, cellIndex) => (
                        <td key={cellIndex} className="border border-gray-300 px-4 py-3 font-mono text-sm">
                          {cell || '---'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        }

        // Skip past the table lines we just processed
        i = j
        continue
      }
    }

    // Not a table line, add to current text
    currentTextLines.push(line)
    i++
  }

  // Flush any remaining text
  flushTextLines()

  // If no tables were found, return simple paragraph
  if (result.length === 0) {
    return <p className="mb-4 text-gray-800 leading-relaxed whitespace-pre-wrap">{question}</p>
  }

  return <div className="space-y-2">{result}</div>
}

export default function ExcelMockInterviewer() {
  const [interviewState, setInterviewState] = useState<InterviewState>({
    sessionId: null,
    candidateName: "",
    positionLevel: "intermediate",
    currentMessage: "",
    currentQuestion: null,
    currentQuestionFormat: "open_ended",
    currentOptions: null,
    isComplete: false,
    assessmentResult: null,
  })

  const [currentAnswer, setCurrentAnswer] = useState("")
  const [selectedMCQAnswer, setSelectedMCQAnswer] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const startInterview = async () => {
    if (!interviewState.candidateName.trim()) return

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${BACKEND_URL}/start-interview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_name: interviewState.candidateName,
          position_level: interviewState.positionLevel,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setInterviewState((prev) => ({
        ...prev,
        sessionId: data.session_id,
        currentMessage: data.message,
        currentQuestion: data.question,
        currentQuestionFormat: data.question_format || "open_ended",
        currentOptions: data.options || null,
      }))
    } catch (error) {
      console.error("Error starting interview:", error)
      setError(
        error instanceof Error ? error.message : "Failed to start interview. Please check if the backend is running.",
      )
    }
    setIsLoading(false)
  }

  const submitAnswer = async () => {
    const answerToSubmit =
      interviewState.currentQuestionFormat === "multiple_choice" ? selectedMCQAnswer : currentAnswer

    if (!answerToSubmit.trim() || !interviewState.sessionId) return

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${BACKEND_URL}/submit-answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: interviewState.sessionId,
          answer: answerToSubmit,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setInterviewState((prev) => ({
        ...prev,
        currentMessage: data.message,
        currentQuestion: data.question,
        currentQuestionFormat: data.question_format || "open_ended",
        currentOptions: data.options || null,
        isComplete: data.is_complete,
        assessmentResult: data.assessment_result,
      }))
      setCurrentAnswer("")
      setSelectedMCQAnswer("")
    } catch (error) {
      console.error("Error submitting answer:", error)
      setError(error instanceof Error ? error.message : "Failed to submit answer")
    }
    setIsLoading(false)
  }

  const getSkillLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case "expert":
        return "bg-green-600"
      case "advanced":
        return "bg-blue-600"
      case "intermediate":
        return "bg-yellow-600"
      default:
        return "bg-gray-600"
    }
  }

  // Error display component
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-red-200">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-red-600" />
            </div>
            <CardTitle className="text-2xl text-red-600">Connection Error</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="text-sm text-gray-600">
                <p className="mb-2">To fix this issue:</p>
                <ol className="list-decimal list-inside space-y-1">
                  <li>Make sure the FastAPI backend is running on port 8000</li>
                  <li>Check that GROQ_API_KEY is set in your environment</li>
                  <li>Verify the backend URL: {BACKEND_URL}</li>
                </ol>
              </div>
              <Button
                onClick={() => {
                  setError(null)
                  setInterviewState((prev) => ({ ...prev, sessionId: null }))
                }}
                className="w-full bg-green-600 hover:bg-green-700"
              >
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Landing Page
  if (!interviewState.sessionId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center">
                <MessageCircle className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Excel Mock Interviewer</h1>
                <p className="text-sm text-gray-600">AI-Powered Excel Skills Interview Practice</p>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 py-12">
          <div className="grid lg:grid-cols-2 gap-12 items-start">
            {/* Left Side - Information */}
            <div className="space-y-8">
              <div>
                <h2 className="text-4xl font-bold text-gray-900 mb-4">
                  Practice Your <span className="text-green-600">Excel Interview</span>
                </h2>
                <p className="text-xl text-gray-600 leading-relaxed">
                  Experience a realistic AI-powered Excel skills interview with both multiple choice and detailed
                  questions. Get personalized feedback and improve your performance.
                </p>
              </div>

              {/* Features Grid */}
              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                    <HelpCircle className="w-6 h-6 text-green-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">Mixed Question Types</h3>
                  <p className="text-gray-600 text-sm">
                    Experience both multiple choice questions and detailed open-ended scenarios.
                  </p>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                    <BarChart3 className="w-6 h-6 text-blue-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">Comprehensive Coverage</h3>
                  <p className="text-gray-600 text-sm">
                    Test your knowledge across formulas, data analysis, charts, and advanced features.
                  </p>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                    <Target className="w-6 h-6 text-purple-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">Adaptive Difficulty</h3>
                  <p className="text-gray-600 text-sm">
                    Questions adjust to your skill level for an optimal interview experience.
                  </p>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                  <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
                    <Calculator className="w-6 h-6 text-orange-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">Instant Scoring</h3>
                  <p className="text-gray-600 text-sm">
                    Get immediate feedback on both MCQ accuracy and detailed explanations.
                  </p>
                </div>
              </div>

              {/* Interview Benefits */}
              <div className="bg-gradient-to-r from-green-600 to-blue-600 p-6 rounded-xl text-white">
                <h3 className="text-xl font-semibold mb-4">What You'll Experience</h3>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 flex-shrink-0" />
                    <span>5+ multiple choice questions for quick knowledge testing</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 flex-shrink-0" />
                    <span>Detailed scenario-based questions requiring explanations</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 flex-shrink-0" />
                    <span>Adaptive questioning that adjusts based on your responses</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 flex-shrink-0" />
                    <span>Professional skill evaluation from Beginner to Expert level</span>
                  </div>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">8-12</div>
                  <div className="text-sm text-gray-600">Questions</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">5+</div>
                  <div className="text-sm text-gray-600">MCQ Questions</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600">15-25</div>
                  <div className="text-sm text-gray-600">Minutes</div>
                </div>
              </div>
            </div>

            {/* Right Side - Interview Form */}
            <div className="lg:sticky lg:top-8">
              <Card className="border-2 border-green-200 shadow-xl">
                <CardHeader className="bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-t-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                      <MessageCircle className="w-6 h-6" />
                    </div>
                    <div>
                      <CardTitle className="text-2xl">Start Your Interview</CardTitle>
                      <CardDescription className="text-green-100">
                        Begin your Excel skills interview practice session
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-8 space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="name" className="text-base font-medium">
                      Full Name
                    </Label>
                    <Input
                      id="name"
                      placeholder="Enter your full name"
                      value={interviewState.candidateName}
                      onChange={(e) => setInterviewState((prev) => ({ ...prev, candidateName: e.target.value }))}
                      className="h-12 text-base border-2 border-gray-200 focus:border-green-500"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="level" className="text-base font-medium">
                      Experience Level
                    </Label>
                    <Select
                      value={interviewState.positionLevel}
                      onValueChange={(value) => setInterviewState((prev) => ({ ...prev, positionLevel: value }))}
                    >
                      <SelectTrigger className="h-12 text-base border-2 border-gray-200 focus:border-green-500">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="beginner">
                          <div className="flex items-center gap-3">
                            <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
                            <div>
                              <div className="font-medium">Beginner</div>
                              <div className="text-sm text-gray-500">0-2 years experience</div>
                            </div>
                          </div>
                        </SelectItem>
                        <SelectItem value="intermediate">
                          <div className="flex items-center gap-3">
                            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                            <div>
                              <div className="font-medium">Intermediate</div>
                              <div className="text-sm text-gray-500">2-5 years experience</div>
                            </div>
                          </div>
                        </SelectItem>
                        <SelectItem value="advanced">
                          <div className="flex items-center gap-3">
                            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                            <div>
                              <div className="font-medium">Advanced</div>
                              <div className="text-sm text-gray-500">5+ years experience</div>
                            </div>
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <div className="flex items-start gap-3">
                      <Users className="w-5 h-5 text-blue-600 mt-0.5" />
                      <div className="text-sm text-blue-800">
                        <p className="font-medium mb-1">Interview Format</p>
                        <p>
                          Mix of multiple choice questions (5+) and detailed scenario questions. Adapts to your skill
                          level.
                        </p>
                      </div>
                    </div>
                  </div>

                  <Button
                    onClick={startInterview}
                    disabled={!interviewState.candidateName.trim() || isLoading}
                    className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 shadow-lg"
                  >
                    {isLoading ? (
                      <div className="flex items-center gap-2">
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        Starting Interview...
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <MessageCircle className="w-5 h-5" />
                        Begin Interview
                      </div>
                    )}
                  </Button>

                  <div className="text-center text-sm text-gray-500">
                    Free • No registration required • Instant feedback
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (interviewState.isComplete && interviewState.assessmentResult) {
    const result = interviewState.assessmentResult
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50 p-4">
        <div className="max-w-4xl mx-auto space-y-6">
          <Card className="border-2 border-green-200">
            <CardHeader className="text-center bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-t-lg">
              <div className="mx-auto mb-4 w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                <CheckCircle className="w-8 h-8" />
              </div>
              <CardTitle className="text-2xl">Interview Complete!</CardTitle>
              <CardDescription className="text-green-100">{result.interview_summary}</CardDescription>
            </CardHeader>
          </Card>

          <div className="grid md:grid-cols-2 gap-6">
            <Card className="border-2 border-green-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                  Overall Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-2">
                      <span>Overall Score</span>
                      <span className="font-semibold">{(result.overall_score * 100).toFixed(0)}%</span>
                    </div>
                    <Progress value={result.overall_score * 100} className="h-3" />
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getSkillLevelColor(result.overall_level)}>{result.overall_level}</Badge>
                    <span className="text-sm text-gray-600">Skill Level</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-2 border-blue-200">
              <CardHeader>
                <CardTitle>Key Strengths</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {result.key_strengths.map((strength: string, index: number) => (
                    <li key={index} className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm">{strength}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>

          <Card className="border-2 border-gray-200">
            <CardHeader>
              <CardTitle>Skill Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-4">
                {result.skill_assessments.map((skill: any, index: number) => (
                  <div key={index} className="p-4 border-2 border-gray-100 rounded-lg bg-white">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-medium">{skill.skill_area}</h4>
                      <Badge className={getSkillLevelColor(skill.level)} variant="secondary">
                        {skill.level}
                      </Badge>
                    </div>
                    <Progress value={skill.score * 100} className="h-2 mb-3" />
                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="font-medium text-green-600">Strengths:</span>
                        <ul className="ml-4 list-disc">
                          {skill.strengths.slice(0, 2).map((strength: string, i: number) => (
                            <li key={i}>{strength}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-2 border-orange-200">
            <CardHeader>
              <CardTitle>Recommendations & Next Steps</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-3">Improvement Areas</h4>
                  <ul className="space-y-2">
                    {result.improvement_recommendations.map((rec: string, index: number) => (
                      <li key={index} className="flex items-start gap-2">
                        <Clock className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium mb-3">Next Steps</h4>
                  <ul className="space-y-2">
                    {result.next_steps.map((step: string, index: number) => (
                      <li key={index} className="flex items-start gap-2">
                        <TrendingUp className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm">{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50 p-4">
      <div className="max-w-2xl mx-auto space-y-6">
        <Card className="border-2 border-green-200">
          <CardHeader className="bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-t-lg">
            <CardTitle>Excel Skills Interview</CardTitle>
            <CardDescription className="text-green-100">
              Answer each question thoroughly. Mix of multiple choice and detailed questions.
            </CardDescription>
          </CardHeader>
        </Card>

        {interviewState.currentMessage && (
          <Card className="border-2 border-blue-200">
            <CardContent className="pt-6">
              <p className="text-gray-700">{interviewState.currentMessage}</p>
            </CardContent>
          </Card>
        )}

        {interviewState.currentQuestion && (
          <Card className="border-2 border-gray-200">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                {interviewState.currentQuestionFormat === "multiple_choice" ? (
                  <HelpCircle className="w-5 h-5 text-blue-600" />
                ) : (
                  <MessageCircle className="w-5 h-5 text-green-600" />
                )}
                {interviewState.currentQuestionFormat === "multiple_choice" ? "Multiple Choice Question" : "Question"}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {renderQuestionWithTables(interviewState.currentQuestion)}

              <div className="space-y-4">
                {interviewState.currentQuestionFormat === "multiple_choice" && interviewState.currentOptions ? (
                  <div className="space-y-3">
                    <RadioGroup value={selectedMCQAnswer} onValueChange={setSelectedMCQAnswer}>
                      {interviewState.currentOptions.map((option, index) => (
                        <div key={index} className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50">
                          <RadioGroupItem value={option.charAt(0)} id={`option-${index}`} />
                          <Label htmlFor={`option-${index}`} className="flex-1 cursor-pointer">
                            {option}
                          </Label>
                        </div>
                      ))}
                    </RadioGroup>
                  </div>
                ) : (
                  <Textarea
                    placeholder="Type your detailed answer here. Be specific about your approach, formulas, or steps you would take..."
                    value={currentAnswer}
                    onChange={(e) => setCurrentAnswer(e.target.value)}
                    rows={6}
                    className="resize-none border-2 border-gray-200 focus:border-green-500"
                  />
                )}

                <Button
                  onClick={submitAnswer}
                  disabled={
                    (interviewState.currentQuestionFormat === "multiple_choice"
                      ? !selectedMCQAnswer
                      : !currentAnswer.trim()) || isLoading
                  }
                  className="w-full h-12 bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700"
                >
                  {isLoading ? (
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Processing Answer...
                    </div>
                  ) : (
                    "Submit Answer"
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
