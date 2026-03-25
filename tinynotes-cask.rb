cask "tinynotes" do
  version "1.0.1"
  sha256 "fdd77930dc313d8a9e9d0d2e1e184444cd8ea44884a530b43c45502d5ca9f432"

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
