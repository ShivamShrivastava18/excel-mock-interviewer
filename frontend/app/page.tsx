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
import { CheckCircle, Clock, FileSpreadsheet, TrendingUp } from "lucide-react"

interface InterviewState {
  sessionId: string | null
  candidateName: string
  positionLevel: string
  currentMessage: string
  currentQuestion: string | null
  isComplete: boolean
  assessmentResult: any | null
}

export default function ExcelAssessmentApp() {
  const [interviewState, setInterviewState] = useState<InterviewState>({
    sessionId: null,
    candidateName: "",
    positionLevel: "intermediate",
    currentMessage: "",
    currentQuestion: null,
    isComplete: false,
    assessmentResult: null,
  })

  const [currentAnswer, setCurrentAnswer] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const startInterview = async () => {
    if (!interviewState.candidateName.trim()) return

    setIsLoading(true)
    try {
      const response = await fetch("/api/start-interview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_name: interviewState.candidateName,
          position_level: interviewState.positionLevel,
        }),
      })

      const data = await response.json()
      setInterviewState((prev) => ({
        ...prev,
        sessionId: data.session_id,
        currentMessage: data.message,
        currentQuestion: data.question,
      }))
    } catch (error) {
      console.error("Error starting interview:", error)
    }
    setIsLoading(false)
  }

  const submitAnswer = async () => {
    if (!currentAnswer.trim() || !interviewState.sessionId) return

    setIsLoading(true)
    try {
      const response = await fetch("/api/submit-answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: interviewState.sessionId,
          answer: currentAnswer,
        }),
      })

      const data = await response.json()
      setInterviewState((prev) => ({
        ...prev,
        currentMessage: data.message,
        currentQuestion: data.question,
        isComplete: data.is_complete,
        assessmentResult: data.assessment_result,
      }))
      setCurrentAnswer("")
    } catch (error) {
      console.error("Error submitting answer:", error)
    }
    setIsLoading(false)
  }

  const getSkillLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case "expert":
        return "bg-green-500"
      case "advanced":
        return "bg-blue-500"
      case "intermediate":
        return "bg-yellow-500"
      default:
        return "bg-gray-500"
    }
  }

  if (!interviewState.sessionId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <FileSpreadsheet className="w-8 h-8 text-green-600" />
            </div>
            <CardTitle className="text-2xl">Excel Skills Assessment</CardTitle>
            <CardDescription>Automated interview system to evaluate your Excel proficiency</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                placeholder="Enter your full name"
                value={interviewState.candidateName}
                onChange={(e) => setInterviewState((prev) => ({ ...prev, candidateName: e.target.value }))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="level">Position Level</Label>
              <Select
                value={interviewState.positionLevel}
                onValueChange={(value) => setInterviewState((prev) => ({ ...prev, positionLevel: value }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="beginner">Beginner (0-2 years)</SelectItem>
                  <SelectItem value="intermediate">Intermediate (2-5 years)</SelectItem>
                  <SelectItem value="advanced">Advanced (5+ years)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={startInterview}
              disabled={!interviewState.candidateName.trim() || isLoading}
              className="w-full"
            >
              {isLoading ? "Starting Interview..." : "Start Assessment"}
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (interviewState.isComplete && interviewState.assessmentResult) {
    const result = interviewState.assessmentResult
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <div className="max-w-4xl mx-auto space-y-6">
          <Card>
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <CardTitle className="text-2xl">Assessment Complete!</CardTitle>
              <CardDescription>{result.interview_summary}</CardDescription>
            </CardHeader>
          </Card>

          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
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

            <Card>
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

          <Card>
            <CardHeader>
              <CardTitle>Skill Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-4">
                {result.skill_assessments.map((skill: any, index: number) => (
                  <div key={index} className="p-4 border rounded-lg">
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

          <Card>
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-2xl mx-auto space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Excel Skills Interview</CardTitle>
            <CardDescription>Answer each question thoroughly. Explain your approach and reasoning.</CardDescription>
          </CardHeader>
        </Card>

        {interviewState.currentMessage && (
          <Card>
            <CardContent className="pt-6">
              <p className="text-gray-700">{interviewState.currentMessage}</p>
            </CardContent>
          </Card>
        )}

        {interviewState.currentQuestion && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Question</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="mb-4 text-gray-800 leading-relaxed">{interviewState.currentQuestion}</p>

              <div className="space-y-4">
                <Textarea
                  placeholder="Type your detailed answer here. Be specific about your approach, formulas, or steps you would take..."
                  value={currentAnswer}
                  onChange={(e) => setCurrentAnswer(e.target.value)}
                  rows={6}
                  className="resize-none"
                />

                <Button onClick={submitAnswer} disabled={!currentAnswer.trim() || isLoading} className="w-full">
                  {isLoading ? "Processing Answer..." : "Submit Answer"}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
