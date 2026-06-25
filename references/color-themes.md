# Color And Theme Reference

Use this file for Taskwarrior color syntax, `task-color(5)`, color rules, themes, terminal behavior, and `_forcecolor`.

## Terminal Behavior

- Taskwarrior disables color automatically when output is redirected to a file or pipe.
- `task show | grep '^color '` can report color as off because the output is piped.
- Force color only when the user needs ANSI color in redirected output:

```bash
task rc._forcecolor=on list > tasks-colored.txt
```

- Persistent `_forcecolor=on` is rarely appropriate. Prefer per-command overrides.

## Inspecting Colors

- `task color` or `task colors` shows available color samples.
- `task color <spec>` previews a specific color combination.
- `task color legend` lists ALL color rules currently in effect: Taskwarrior's compiled-in defaults merged with any taskrc/theme overrides and additions (~47 built-in rules). It is the canonical way to enumerate the effective rule set, BUT captured/piped (non-TTY, i.e. how an agent runs) it prints only a "color is turned off" message and exits `1` — for agent enumeration always force color: `task rc._forcecolor=on color legend`.

Examples:

```bash
task rc._forcecolor=on colors
task rc._forcecolor=on color underline bold red on black
task rc._forcecolor=on color legend
```

## 16-Color Syntax

- Basic named colors: `black`, `red`, `blue`, `green`, `magenta`, `cyan`, `yellow`, `white`.
- Foreground uses the color name alone: `green`.
- Background uses `on`: `green on yellow`, `on yellow`.
- Attributes include `bold`, `bright` for background colors, `underline`, and `inverse`.
- Word order is flexible except `on` separates foreground and background.
- Quote multi-word color values in shell commands.

Examples:

```bash
task rc.confirmation=off config color.project.Home 'on blue'
task rc.confirmation=off config color.keyword.clean 'bold yellow'
task rc.confirmation=off config color.warning 'bold red'
```

## 256-Color Syntax

- Ordinal colors: `color0` through `color255`.
- RGB cube colors: `rgb000` through `rgb555`, where each component is 0-5.
- Gray ramp: `gray0` through `gray23`.
- 16-color names can be mixed with 256-color names, but visual results vary by terminal.
- `bold` and `bright` do not apply to 256-color values; `underline` still applies.

Examples:

```bash
task color black on rgb515
task rc.confirmation=off config color.tag.billing 'rgb005'
task rc.confirmation=off config color.project.Work 'black on gray3'
```

## Color Rules

- Color rules are config variables whose values are color specs.
- Rules can target task state, project, tag, keyword, UDA presence/value, report labels, calendar states, graphs, sync, and debug output.
- Setting, changing, or clearing any color rule via `task config color.X 'spec'` (and `rule.color.merge`) is a config write, so it triggers a yes/no confirmation. With no TTY the prompt defaults to "no", prints "No changes made.", writes nothing, and still exits 0 (silent no-op). Agents must prefix `rc.confirmation=off`. See agent-runtime-safety.md.
- Disable a default rule (these compiled-in defaults are why `color legend` is non-empty) by setting it blank:

```bash
task rc.confirmation=off config color.tagged ''
```

- Common scoped rules:

```text
color.project.<project>
color.project.none
color.tag.<tag>
color.tag.none
color.keyword.<word>
color.uda.<name>
color.uda.<name>.<value>
color.uda.<name>.none
```

- Color rules normally merge. If merging produces poor combinations, disable merging:

```bash
task rc.confirmation=off config rule.color.merge no
```

- `rule.precedence.color` controls which color rules win when merging is disabled or precedence matters. The list omits the `color.` prefix and uses prefixes such as `keyword.`, `tag.`, `project.`, and `uda.` for wildcard groups.
- The default is `deleted,completed,active,keyword.,tag.,project.,overdue,scheduled,due.today,due,blocked,blocking,recurring,tagged,uda.` (highest precedence first; `color.deleted` wins, `color.uda.` loses). Edit from this baseline to reorder, e.g. move a tag ahead of `overdue`.

## Themes

- Themes are taskrc include files containing color rules.
- Include a theme from taskrc with:

```text
include dark-256.theme
```

- Standard theme names include `dark-16.theme` and `dark-256.theme`.
- `include` path resolution follows taskrc rules: current directory, taskrc directory, then package-managed theme directories.
- Prefer explaining theme includes over manually recreating many color rules.
