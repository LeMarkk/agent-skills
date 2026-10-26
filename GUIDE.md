# A beginner's guide to building with Claude Code and devkit

This guide is for you if you want to build an app or a website with Claude Code but you aren't a programmer, or you're just starting out. You don't need to know how to code. You need about 30 minutes for the setup, and you'll type a few commands that you can copy and paste from here.

## What devkit does for you

Claude Code is an AI assistant that works inside your project folder: it writes code, runs commands and fixes problems. That's powerful, and it means a wrong command can delete files or data. devkit adds three helpers:

- **guard, the seatbelt.** Before Claude runs any command or changes any file, guard checks it. Things that can destroy work, such as deleting your whole folder, are stopped. Risky things, such as wiping a database, make Claude Code ask you first. Everyday work goes through without interruptions.
- **debug, the detective.** When something breaks, it makes Claude find the real cause and prove it before changing code, instead of guessing. After three wrong guesses it stops and tells you what it tried, rather than going in circles.
- **setup, the installer.** It adds devkit to a project and writes extra rules that fit what you're building.

devkit can't make mistakes impossible. It catches the common, costly ones, and it always lets *you* make the final call.

## What you need

- A computer running macOS 13 or later, Windows 10 or 11, or Linux (Ubuntu 20.04 or later, Debian 10 or later).
- A paid Claude plan: Pro, Max, Team or Enterprise. The free plan doesn't include Claude Code.
- An internet connection.

devkit is tested on macOS and Linux. It should work on Windows with the steps below, but it hasn't been tested there yet; if something doesn't work, please [open an issue](https://github.com/LeMarkk/agent-skills/issues).

## Step 1. Open a terminal

The terminal is a window where you type commands instead of clicking. You only need it for setup and to start Claude Code.

- **Mac:** press `Cmd` + `Space`, type **Terminal**, press `Enter`.
- **Windows:** click Start, type **PowerShell**, open **Windows PowerShell**.
- **Linux:** open the **Terminal** app.

To run a command from this guide: copy it, paste it into the terminal, and press `Enter`. If you've never done this, Anthropic's [terminal guide](https://code.claude.com/docs/en/terminal-guide) walks through it with pictures.

## Step 2. Install Git and Python

devkit uses two free tools: **Git**, which keeps a history of your project so you can undo changes, and **Python**, which runs guard.

**Mac.** Run this, then click **Install** in the window that appears:

```sh
xcode-select --install
```

If it says the tools are already installed, you're done.

**Windows.**

1. Install [Git for Windows](https://git-scm.com/downloads/win). The default options are fine.
2. Install Python from [python.org/downloads](https://www.python.org/downloads/). On the first installer screen, tick **Add python.exe to PATH** before clicking **Install Now**.
3. Close PowerShell and open it again so it finds the new tools.

**Linux (Ubuntu or Debian).**

```sh
sudo apt install git python3
```

**Check it worked.** Each of these should print a version number:

```sh
git --version
python3 --version
```

On Windows, use `python --version` instead of `python3 --version`. Any Python from 3.8 on is fine.

## Step 3. Install Claude Code

**Mac or Linux:**

```sh
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://claude.ai/install.ps1 | iex
```

The installer shows no progress while it downloads; give it a minute. Then **close the terminal, open a new one**, and check:

```sh
claude --version
```

You should see a version number. If you see "command not found" or "not recognized", see [Fix your PATH](https://code.claude.com/docs/en/troubleshoot-install) in Anthropic's docs.

**Log in** by running `claude` once and following the steps in your browser. Then type `/exit` to close it.

Prefer not to use the terminal day to day? The [Claude desktop app](https://code.claude.com/docs/en/desktop-quickstart) runs Claude Code in a normal window. You still need the terminal once, for Step 4; after that, devkit works in the desktop app too.

## Step 4. Install devkit

Paste these two lines, one at a time:

```sh
claude plugin marketplace add LeMarkk/agent-skills
claude plugin install devkit@lemarkk
```

The first adds this collection of skills to Claude Code, and the second installs devkit from it. Check it:

```sh
claude plugin list
```

You should see `devkit@lemarkk` with `Status: enabled`. devkit is now on for every project on your computer.

## Step 5. Start your first project

Make a folder for the project and start Claude Code inside it. Change `my-first-app` to any name, without spaces:

```sh
mkdir my-first-app
cd my-first-app
git init
claude
```

`git init` turns on the project history. Now, inside Claude Code, type:

```
/devkit:setup
```

Claude adds devkit to the project and shows you any extra rules it suggests. Read them and say yes if they make sense. Run `/devkit:setup` again later, once your project has a database or a deploy step, so the rules can catch up.

Then describe what you want to build, in plain words. For example:

> Build a simple website for my bakery: a home page, a menu page with prices, and a contact form that emails me. Keep it simple and explain what you're doing as you go.

> I want a to-do list app I can use on my phone. Start with the smallest version that works, then we'll add features.

Ask for one small piece at a time. Check that it works before asking for the next.

## Working with Claude day to day

### When Claude Code asks permission

Claude Code asks before running commands and changing files. Read what it wants to do before saying yes. If you don't understand a command, answer no and ask: *"What does that command do, in plain words?"*

### When guard steps in

guard's messages start with `[guard]`:

| What you see | What it means | What to do |
|---|---|---|
| `[guard] Needs your OK: …` | The command could delete work or data, but is sometimes the right thing to do. | Read the reason. If you're not sure, say no and ask Claude for a safer way, such as *"show me what this would delete first"*. |
| `[guard] Blocked: …` | The command is almost never what anyone wants, such as deleting your whole home folder. | Don't look for a way around it. Ask Claude what it was trying to achieve and do it another way. |

devkit tells Claude not to reword a command to slip past guard. If it ever tries, stop it and say so.

### When something breaks

Type `/devkit:debug`, then paste the error or describe what went wrong:

```
/devkit:debug The contact form shows "500 error" when I press Send.
```

Claude will reproduce the problem, find the cause, write a test that shows the bug, fix it, and finish with a short **debug report**. The lines to read are **Root cause** (what was wrong), **Fix** (what changed) and **Status**:

- `DONE`: fixed and checked.
- `DONE_WITH_CONCERNS`: fixed, with something it wants you to know.
- `BLOCKED`: it didn't find the cause after three tries, and tells you what it learned and what it suggests next.

### Keeping Claude focused

If you only want one part of the project changed, say so:

> Only change files in the `website` folder. Lock edits to it while we work.

That turns on guard's edit lock, which blocks changes anywhere else until you say *"unlock edits"*.

### Saving your work

After each change that works, ask Claude:

> Commit this with a short message describing what changed.

Each commit is a save point you can go back to. For a backup outside your computer, ask Claude to help you put the project on GitHub.

## Safety habits worth keeping

- **Never paste passwords, API keys or card numbers into the chat.** Put keys in a `.env` file and ask Claude to make sure it's in `.gitignore`, so it never goes into Git or onto GitHub.
- **Use test mode** for payments, email and other paid services until you're ready to go live.
- **Keep real customer data out of your test project.** Use made-up examples.
- **Read before you approve.** guard catches the common disasters, but you're the final check.
- **Commit often.** It's the easiest way to undo a bad change.

## Keeping devkit up to date

To get the latest version:

```sh
claude plugin update devkit@lemarkk
```

Or let it update itself: in Claude Code, type `/plugin`, go to the **Marketplaces** tab, select **lemarkk**, and choose **Enable auto-update**.

## If something goes wrong

| Problem | Fix |
|---|---|
| `claude: command not found` | Close the terminal and open a new one. If it still fails, see [Troubleshoot installation](https://code.claude.com/docs/en/troubleshoot-install). |
| `devkit@lemarkk` isn't in `claude plugin list` | Run both commands in Step 4 again. |
| Claude Code shows a hook error before every command | Python isn't installed or can't be found. Repeat Step 2, then open a new terminal. Until it's fixed, guard isn't checking anything. |
| `/devkit:setup` or `/devkit:debug` isn't recognised | Type `/exit` and start `claude` again, or type `/reload-plugins`. |
| guard keeps asking about something you do all the time | Ask Claude to add an `allow` rule for that exact command to `.claude/guard.json`. Keep it narrow. |

Still stuck? Open an issue at [github.com/LeMarkk/agent-skills/issues](https://github.com/LeMarkk/agent-skills/issues) with what you typed and what you saw. Leave out passwords and keys.

## Words you'll see

- **Terminal:** the window where you type commands.
- **Command:** an instruction typed into the terminal, like `git init`.
- **Project folder** or **repository (repo):** the folder that holds everything for one app.
- **Git:** the tool that records your project's history.
- **Commit:** a save point in that history.
- **GitHub:** a website that stores a copy of your repository online.
- **Plugin:** an add-on for Claude Code. devkit is one.
- **Skill:** a set of instructions Claude follows for a kind of task, such as debugging. You can call one by name, like `/devkit:debug`.
- **Hook:** a small program Claude Code runs automatically at certain moments. guard is a hook that runs before every command.
- **Database:** where an app stores its data, such as users and orders.
- **Migration:** a file that changes the shape of a database. Once one has run, it should never be edited; you add a new one instead.
- **`.env` file:** a file for secret settings like API keys. It should never be committed.
- **Deploy:** putting your app online so other people can use it.
