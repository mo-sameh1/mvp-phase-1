from agents.runtime.filesystem import RuntimePaths, build_runtime_backend


def runtime_paths(tmp_path) -> RuntimePaths:
    evidence_root = tmp_path / "evidence"
    systems_root = tmp_path / "model-repo" / "systems"
    skills_root = tmp_path / "skills"
    evidence_root.mkdir(parents=True)
    systems_root.mkdir(parents=True)
    skills_root.mkdir(parents=True)
    return RuntimePaths(
        evidence_root=evidence_root,
        model_repo_checkout=tmp_path / "model-repo",
        skills_root=skills_root,
    )


def test_evidence_route_is_readable_but_not_writable(tmp_path):
    paths = runtime_paths(tmp_path)
    (paths.evidence_root / "interview.txt").write_text("payment process", encoding="utf-8")
    backend = build_runtime_backend(paths)

    read = backend.read("/evidence/interview.txt")
    write = backend.write("/evidence/new.txt", "not allowed")
    edit = backend.edit("/evidence/interview.txt", "payment", "billing")

    assert read.error is None
    assert read.file_data["content"] == "payment process"
    assert "not allowed" in write.error
    assert "not allowed" in edit.error
    assert not (paths.evidence_root / "new.txt").exists()


def test_evidence_route_supports_glob_and_grep(tmp_path):
    paths = runtime_paths(tmp_path)
    (paths.evidence_root / "strategy.md").write_text("target architecture", encoding="utf-8")
    backend = build_runtime_backend(paths)

    glob = backend.glob("*.md", path="/evidence/")
    grep = backend.grep("target", path="/evidence/")

    assert glob.error is None
    assert [match["path"] for match in glob.matches] == ["/evidence/strategy.md"]
    assert grep.error is None
    assert grep.matches[0]["path"] == "/evidence/strategy.md"


def test_systems_route_writes_to_model_repo_checkout(tmp_path):
    paths = runtime_paths(tmp_path)
    backend = build_runtime_backend(paths)

    result = backend.write(
        "/systems/demo-legacy-system/as-is/application/payment-service.json",
        '{"id": "payment-service"}',
    )

    assert result.error is None
    written = (
        paths.model_repo_checkout
        / "systems"
        / "demo-legacy-system"
        / "as-is"
        / "application"
        / "payment-service.json"
    )
    assert written.read_text(encoding="utf-8") == '{"id": "payment-service"}'


def test_skills_route_is_readable_but_not_writable(tmp_path):
    paths = runtime_paths(tmp_path)
    skill_dir = paths.skills_root / "archimate-metamodel"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: archimate-metamodel\n---\n", encoding="utf-8")
    backend = build_runtime_backend(paths)

    read = backend.read("/skills/archimate-metamodel/SKILL.md")
    write = backend.write("/skills/archimate-metamodel/notes.md", "not allowed")

    assert read.error is None
    assert "archimate-metamodel" in read.file_data["content"]
    assert "not allowed" in write.error
    assert not (skill_dir / "notes.md").exists()
