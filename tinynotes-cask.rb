cask "tinynotes" do
  version "1.0.2"
  sha256 "0ac008488711dc2e2684cfad53f462a7d22f96bb64c7e1bce6723f29771163ff"

  url "https://github.com/msempere/tinynotes/releases/download/v#{version}/TinyNotes-#{version}.zip"
  name "TinyNotes"
  desc "Simple macOS menu bar app for quick note-taking"
  homepage "https://github.com/msempere/tinynotes"

  livecheck do
    url :url
    strategy :github_latest
  end

  app "TinyNotes.app"

  postflight do
    system_command "/usr/bin/xattr",
                   args: ["-dr", "com.apple.quarantine", "#{appdir}/TinyNotes.app"],
                   sudo: false
  end

  zap trash: [
    "~/TinyNotes",
  ]
end
