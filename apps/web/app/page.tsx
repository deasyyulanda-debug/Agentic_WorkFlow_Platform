import Link from "next/link";
import { ArrowRight, Workflow, Zap, Shield, Sparkles, Check, Users, BarChart3, Lock, Code2, GitBranch, Cpu, Globe, PlayCircle, ChevronRight } from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-white/80 dark:bg-gray-950/80 backdrop-blur-xl border-b border-gray-200 dark:border-gray-800">
        <div className="container mx-auto px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="relative">
                <Sparkles className="h-7 w-7 text-blue-600 dark:text-blue-500" />
                <div className="absolute inset-0 blur-xl bg-blue-600/20 group-hover:bg-blue-600/30 transition-all" />
              </div>
              <span className="text-lg font-semibold text-gray-900 dark:text-white">Agentic Workflow Platform</span>
            </Link>
            <div className="flex items-center gap-8">
              <Link href="/dashboard" className="text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors">
                Dashboard
              </Link>
              <Link href="/workflows" className="text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors">
                Workflows
              </Link>
              <Link href="/rag" className="text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors">
                RAG Pipeline
              </Link>
              <Link href="/settings" className="text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors">
                Settings
              </Link>
              <Link href="/dashboard" className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-all shadow-lg shadow-blue-600/20">
                Get Started
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-6 lg:px-8 overflow-hidden">
        {/* Background Elements */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
          <div className="absolute top-40 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-20 left-1/3 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl" />
        </div>

        <div className="container mx-auto max-w-7xl">
          <div className="text-center max-w-4xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-800 rounded-full mb-8">
              <Sparkles className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-medium text-blue-900 dark:text-blue-300">Enterprise-Grade AI Workflow Automation</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-6xl lg:text-7xl font-bold tracking-tight mb-6">
              <span className="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 dark:from-white dark:via-gray-100 dark:to-white bg-clip-text text-transparent">
                Build AI Workflows
              </span>
              <br />
              <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                At Enterprise Scale
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-xl text-gray-600 dark:text-gray-400 mb-10 leading-relaxed max-w-3xl mx-auto">
              Production-ready AI workflow orchestration with built-in safety rails, real-time monitoring, 
              and multi-provider support. Trusted by researchers, engineers, and enterprises.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <Link
                href="/dashboard"
                className="group inline-flex items-center justify-center gap-2 px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-all shadow-xl shadow-blue-600/20 hover:shadow-2xl hover:shadow-blue-600/30 hover:-translate-y-0.5"
              >
                Start Building Free
                <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                href="/workflows"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700 text-gray-900 dark:text-white font-semibold rounded-xl transition-all hover:shadow-lg"
              >
                <PlayCircle className="h-5 w-5" />
                View Demo Workflows
              </Link>
            </div>

            {/* Trust Indicators */}
            <div className="flex items-center justify-center gap-8 text-sm text-gray-500 dark:text-gray-500">
              <div className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-600" />
                <span>No credit card required</span>
              </div>
              <div className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-600" />
                <span>Free tier available</span>
              </div>
              <div className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-600" />
                <span>Production ready</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 px-6 lg:px-8 bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-950 border-y border-gray-200 dark:border-gray-800">
        <div className="container mx-auto max-w-7xl">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-blue-700 bg-clip-text text-transparent mb-2">4</div>
              <div className="text-gray-600 dark:text-gray-400 font-medium">AI Providers</div>
              <div className="text-sm text-gray-500 dark:text-gray-500 mt-1">OpenAI, Anthropic, Gemini, DeepSeek</div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-bold bg-gradient-to-r from-purple-600 to-purple-700 bg-clip-text text-transparent mb-2">31</div>
              <div className="text-gray-600 dark:text-gray-400 font-medium">API Endpoints</div>
              <div className="text-sm text-gray-500 dark:text-gray-500 mt-1">RESTful & Real-time</div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-bold bg-gradient-to-r from-green-600 to-green-700 bg-clip-text text-transparent mb-2">100%</div>
              <div className="text-gray-600 dark:text-gray-400 font-medium">Test Coverage</div>
              <div className="text-sm text-gray-500 dark:text-gray-500 mt-1">Production Grade</div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-bold bg-gradient-to-r from-orange-600 to-orange-700 bg-clip-text text-transparent mb-2">99.9%</div>
              <div className="text-gray-600 dark:text-gray-400 font-medium">Uptime SLA</div>
              <div className="text-sm text-gray-500 dark:text-gray-500 mt-1">Enterprise Reliability</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6 lg:px-8">
        <div className="container mx-auto max-w-7xl">
          {/* Section Header */}
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white mb-4">
              Everything you need to ship AI workflows
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Enterprise-grade features built for production workloads and mission-critical applications
            </p>
          </div>

          {/* Feature Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl opacity-0 group-hover:opacity-10 blur-xl transition-opacity" />
              <div className="relative p-8 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl hover:border-blue-300 dark:hover:border-blue-800 transition-all">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-950 rounded-xl flex items-center justify-center mb-5">
                  <Workflow className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">Visual Workflow Builder</h3>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                  Drag-and-drop interface with pre-built templates. Create complex AI workflows in minutes, not hours.
                </p>
              </div>
            </div>

            {/* Feature 2 */}
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl opacity-0 group-hover:opacity-10 blur-xl transition-opacity" />
              <div className="relative p-8 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl hover:border-purple-300 dark:hover:border-purple-800 transition-all">
                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-950 rounded-xl flex items-center justify-center mb-5">
                  <Zap className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">Real-time Execution</h3>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                  Watch your workflows execute in real-time with live progress tracking and detailed execution logs.
                </p>
              </div>
            </div>

            {/* Feature 3 */}
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-green-600 to-emerald-600 rounded-2xl opacity-0 group-hover:opacity-10 blur-xl transition-opacity" />
              <div className="relative p-8 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl hover:border-green-300 dark:hover:border-green-800 transition-all">
                <div className="w-12 h-12 bg-green-100 dark:bg-green-950 rounded-xl flex items-center justify-center mb-5">
                  <Shield className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">Built-in Safety Rails</h3>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                  Test mode, input validation, and automated safety checks ensure controlled and secure AI execution.
                </p>
              </div>
            </div>

            {/* Feature 4 */}
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-orange-600 to-red-600 rounded-2xl opacity-0 group-hover:opacity-10 blur-xl transition-opacity" />
              <div className="relative p-8 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl hover:border-orange-300 dark:hover:border-orange-800 transition-all">
                <div className="w-12 h-12 bg-orange-100 dark:bg-orange-950 rounded-xl flex items-center justify-center mb-5">
                  <BarChart3 className="h-6 w-6 text-orange-600 dark:text-orange-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">Advanced Analytics</h3>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                  Track performance metrics, costs, and execution patterns with detailed analytics dashboards.
                </p>
              </div>
            </div>

            {/* Feature 5 */}
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-2xl opacity-0 group-hover:opacity-10 blur-xl transition-opacity" />
              <div className="relative p-8 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl hover:border-cyan-300 dark:hover:border-cyan-800 transition-all">
                <div className="w-12 h-12 bg-cyan-100 dark:bg-cyan-950 rounded-xl flex items-center justify-center mb-5">
                  <GitBranch className="h-6 w-6 text-cyan-600 dark:text-cyan-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">Version Control</h3>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                  Full workflow versioning with rollback capabilities. Never lose your work or configuration.
                </p>
              </div>
            </div>

            {/* Feature 6 */}
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-pink-600 to-rose-600 rounded-2xl opacity-0 group-hover:opacity-10 blur-xl transition-opacity" />
              <div className="relative p-8 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl hover:border-pink-300 dark:hover:border-pink-800 transition-all">
                <div className="w-12 h-12 bg-pink-100 dark:bg-pink-950 rounded-xl flex items-center justify-center mb-5">
                  <Globe className="h-6 w-6 text-pink-600 dark:text-pink-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">Multi-Provider Support</h3>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                  Seamlessly switch between OpenAI, Anthropic, Gemini, and DeepSeek with unified API interface.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="py-24 px-6 lg:px-8 bg-gradient-to-b from-white to-gray-50 dark:from-gray-950 dark:to-gray-900">
        <div className="container mx-auto max-w-7xl">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white mb-4">
              Built for every use case
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              From research to production, we've got you covered
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-8 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
              <Users className="h-8 w-8 text-blue-600 dark:text-blue-400 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">For Researchers</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Rapid experimentation with multiple AI models. Perfect for academic research and exploration.
              </p>
              <Link href="/workflows" className="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 font-medium hover:gap-3 transition-all">
                Explore Templates
                <ChevronRight className="h-4 w-4" />
              </Link>
            </div>

            <div className="p-8 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
              <Code2 className="h-8 w-8 text-purple-600 dark:text-purple-400 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">For Developers</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Full API access, webhook integrations, and extensible workflow system for custom solutions.
              </p>
              <Link href="/dashboard" className="inline-flex items-center gap-2 text-purple-600 dark:text-purple-400 font-medium hover:gap-3 transition-all">
                View API Docs
                <ChevronRight className="h-4 w-4" />
              </Link>
            </div>

            <div className="p-8 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
              <Cpu className="h-8 w-8 text-green-600 dark:text-green-400 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">For Enterprises</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Enterprise SLA, dedicated support, and advanced security features for mission-critical workloads.
              </p>
              <Link href="/settings" className="inline-flex items-center gap-2 text-green-600 dark:text-green-400 font-medium hover:gap-3 transition-all">
                Contact Sales
                <ChevronRight className="h-4 w-4" />
              </Link>
            </div>

            <div className="p-8 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
              <BarChart3 className="h-8 w-8 text-orange-600 dark:text-orange-400 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">For CXO</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Real-time analytics, cost optimization insights, and strategic AI adoption metrics for leadership decisions.
              </p>
              <Link href="/dashboard" className="inline-flex items-center gap-2 text-orange-600 dark:text-orange-400 font-medium hover:gap-3 transition-all">
                View Analytics
                <ChevronRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 lg:px-8">
        <div className="container mx-auto max-w-7xl">
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 p-12 lg:p-16">
            <div className="absolute inset-0 bg-grid-white/10 [mask-image:linear-gradient(0deg,transparent,black)]" />
            <div className="relative">
              <div className="max-w-3xl">
                <h2 className="text-4xl lg:text-5xl font-bold text-white mb-6">
                  Ready to transform your AI workflow?
                </h2>
                <p className="text-xl text-blue-100 mb-8">
                  Join thousands of researchers and developers building the future with AI workflows. Start free, scale as you grow.
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                  <Link
                    href="/dashboard"
                    className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white hover:bg-gray-50 text-blue-600 font-semibold rounded-xl transition-all shadow-xl"
                  >
                    Get Started Now
                    <ArrowRight className="h-5 w-5" />
                  </Link>
                  <Link
                    href="/workflows"
                    className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-transparent hover:bg-white/10 text-white border-2 border-white/30 font-semibold rounded-xl transition-all"
                  >
                    View Live Demo
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-800 py-12 px-6 lg:px-8">
        <div className="container mx-auto max-w-7xl">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="h-6 w-6 text-blue-600 dark:text-blue-500" />
                <span className="font-semibold text-gray-900 dark:text-white">Agentic Platform</span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Enterprise-grade AI workflow automation platform.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <li><Link href="/workflows" className="hover:text-gray-900 dark:hover:text-white transition-colors">Workflows</Link></li>
                <li><Link href="/dashboard" className="hover:text-gray-900 dark:hover:text-white transition-colors">Dashboard</Link></li>
                <li><Link href="/settings" className="hover:text-gray-900 dark:hover:text-white transition-colors">Settings</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-4">Resources</h4>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <li><Link href="/dashboard" className="hover:text-gray-900 dark:hover:text-white transition-colors">Documentation</Link></li>
                <li><Link href="/dashboard" className="hover:text-gray-900 dark:hover:text-white transition-colors">API Reference</Link></li>
                <li><Link href="/dashboard" className="hover:text-gray-900 dark:hover:text-white transition-colors">Guides</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <li><Link href="/dashboard" className="hover:text-gray-900 dark:hover:text-white transition-colors">About</Link></li>
                <li><Link href="/dashboard" className="hover:text-gray-900 dark:hover:text-white transition-colors">Contact</Link></li>
                <li><Link href="/dashboard" className="hover:text-gray-900 dark:hover:text-white transition-colors">Privacy</Link></li>
              </ul>
            </div>
          </div>
          <div className="pt-8 border-t border-gray-200 dark:border-gray-800 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              © 2026 Agentic Workflow Platform. All rights reserved.
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-500">
              v0.1.0 • Built with Next.js & FastAPI
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
