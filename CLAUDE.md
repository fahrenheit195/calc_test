# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

`calc_test` is a minimal Java Swing desktop calculator built with the IntelliJ IDEA GUI Designer. It has a single window with two input fields (A, B), a "Разделить А на Б" (Divide A by B) button, and a result field (C) that shows `A / B`. All UI text and Javadoc comments in the source are in Russian.

There is no build tool (no Maven `pom.xml`, no Gradle build script, no Ant `build.xml`). The project is defined entirely by the IntelliJ module file `calc.iml` and is meant to be opened and run from IntelliJ IDEA.

## Repository structure

- `src/calc/form1.java` — the application entry point and only application class. Contains `main()`, the button click handler, and the division/validation logic.
- `src/calc/form1.form` — the IntelliJ GUI Designer form (XML) that lays out `panel1` and binds its child components (`button1`, `textField1`, `textField2`, `textField3`) to fields in `form1.java` by name. **`form1.java` and `form1.form` must be edited together** — the `.form` file's `binding` attributes must match field names in the Java class, and IntelliJ's form compiler generates the layout code from the `.form` file at build time (it is not present as source).
- `src/tests/test.java` — TestNG test class (`import org.testng.annotations.Test`) with two tests for `form1.division()`.
- `calc.iml` — IntelliJ module descriptor. Declares `src` as the source root (tests are not in a separate source root) and references TestNG/JUnit5 libraries via `$APPLICATION_HOME_DIR$/plugins/...` — i.e. the jars bundled with the local IntelliJ IDEA installation, not jars checked into the repo or fetched by a package manager.
- `out/production/calc/` — committed compiler output (`.class` files), including IntelliJ's `com.intellij.uiDesigner.core.*` runtime classes that `form1`'s generated layout code depends on at runtime. Treat this as a build artifact, not source; it will typically be stale relative to `src/`.

## Working in this codebase

Because there is no Maven/Gradle wrapper, tooling in this repo works differently from a typical Java project:

- **Building/running via `javac`/`java` directly will not work out of the box.** `form1.form` requires the IntelliJ GUI Designer runtime (`com.intellij.uiDesigner.core.*`) on the classpath to instantiate `panel1`'s layout, and `test.java` requires TestNG — neither is vendored in the repo; both come from the local IDE installation (see `calc.iml`). If you need to compile/run outside the IDE, you must supply these jars (e.g. IntelliJ's `uiDesigner.jar` and a TestNG jar) on the classpath yourself.
- **The intended workflow is via IntelliJ IDEA**: open the module, edit `form1.form` in the GUI Designer (or hand-edit the XML) and `form1.java` in the editor together, run `form1.main()` to launch the app, and run `test.java` via the IDE's TestNG runner.
- When changing the UI layout or adding/renaming/removing a bound component, update both `form1.form` (the `binding` attribute and `<constraints>`) and the corresponding private field in `form1.java` — they must stay in sync or the form will fail to bind at runtime.

## Key logic

`form1.java` has three pieces of logic worth understanding before modifying it:

- `numCheck(String)` — validates that a text field contains a number (regex `([-+])?\d*\.?\d+`) before attempting to parse it.
- `division(float a, float b)` — performs `a / b`, writes the result into `textField3`, and returns it.
- `resCheck(String)` — checks the *text already written to* `textField3` for `"nfi"` (substring of `"Infinity"`) or `"NaN"` to detect division-by-zero/zero-by-zero *after* `division()` has already run and written its output.

The button handler in the `form1()` constructor chains these: validate inputs with `numCheck`, call `division()` if valid, then always calls `resCheck` on whatever is currently in `textField3` — including on the validation-error path, since there is no `return`/`else` guarding that final check.
